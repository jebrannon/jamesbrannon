"""Storage service — saves post images, block images, and favicons to S3/MinIO or local filesystem."""
import io
import logging
import os
from pathlib import Path
from typing import List, Tuple

from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

# Local filesystem fallback (used when S3_BUCKET is not set)
POST_IMAGES_DIR = Path(__file__).parent.parent.parent / "static" / "post-images"
POST_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
FAVICON_DIR = Path(__file__).parent.parent.parent / "static" / "favicons"
FAVICON_DIR.mkdir(parents=True, exist_ok=True)

THUMB_SIZE = (1200, 630)
EXPECTED_FAVICON_SIZES = [16, 32, 192, 512]

_S3_BUCKET = os.getenv("S3_BUCKET", "")
_S3_BUCKET_REGION = os.getenv("S3_BUCKET_REGION", "eu-west-2")
_S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL", "") or None   # MinIO in local dev; empty for real AWS
_S3_PUBLIC_BASE_URL = os.getenv("S3_PUBLIC_BASE_URL", "").rstrip("/")
_USE_S3 = bool(_S3_BUCKET)

# cairosvg is optional — installed via requirements-optional.txt
try:
    import cairosvg as _cairosvg
    _CAIROSVG = True
except (ImportError, OSError):
    _CAIROSVG = False


def _get_s3_client():
    import boto3
    return boto3.client(
        "s3",
        region_name=_S3_BUCKET_REGION,
        endpoint_url=_S3_ENDPOINT_URL,
    )


def _public_url(key: str) -> str:
    """Return the public URL for a stored object key."""
    if _S3_PUBLIC_BASE_URL:
        return f"{_S3_PUBLIC_BASE_URL}/{key}"
    return f"https://{_S3_BUCKET}.s3.{_S3_BUCKET_REGION}.amazonaws.com/{key}"


def _upload_to_s3(data: bytes, key: str, content_type: str) -> str:
    """Upload bytes to S3/MinIO and return the public URL."""
    s3 = _get_s3_client()
    s3.put_object(
        Bucket=_S3_BUCKET,
        Key=key,
        Body=data,
        ContentType=content_type,
    )
    return _public_url(key)


def ensure_s3_bucket_exists() -> None:
    """Create the S3/MinIO bucket if it doesn't exist. No-op when S3 is not configured."""
    if not _USE_S3:
        return
    s3 = _get_s3_client()
    try:
        s3.head_bucket(Bucket=_S3_BUCKET)
        return
    except Exception:
        pass
    try:
        if _S3_BUCKET_REGION == "us-east-1":
            s3.create_bucket(Bucket=_S3_BUCKET)
        else:
            s3.create_bucket(
                Bucket=_S3_BUCKET,
                CreateBucketConfiguration={"LocationConstraint": _S3_BUCKET_REGION},
            )
        # Make bucket public-read when using MinIO locally so URLs resolve without auth
        if _S3_ENDPOINT_URL:
            import json
            s3.put_bucket_policy(
                Bucket=_S3_BUCKET,
                Policy=json.dumps({
                    "Version": "2012-10-17",
                    "Statement": [{
                        "Effect": "Allow",
                        "Principal": "*",
                        "Action": "s3:GetObject",
                        "Resource": f"arn:aws:s3:::{_S3_BUCKET}/*",
                    }],
                }),
            )
    except Exception as exc:
        logger.warning("Could not create S3 bucket %s: %s", _S3_BUCKET, exc)


def save_hero_image(image_bytes: bytes, slug: str, ext: str) -> Tuple[str, str]:
    """
    Save the uploaded image and generate a 1200×630 JPEG thumbnail.

    Returns:
        (hero_url, thumbnail_url) — S3/MinIO URLs or relative /static/... paths
    """
    thumb_buf = io.BytesIO()
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img = ImageOps.fit(img, THUMB_SIZE, Image.LANCZOS)
    img.save(thumb_buf, "JPEG", quality=85)
    thumb_bytes = thumb_buf.getvalue()

    if _USE_S3:
        ext_ct = "image/jpeg" if ext.lower() in {".jpg", ".jpeg"} else "image/png"
        hero_url = _upload_to_s3(image_bytes, f"post-images/{slug}-hero{ext}", ext_ct)
        thumb_url = _upload_to_s3(thumb_bytes, f"post-images/{slug}-thumb.jpg", "image/jpeg")
        return hero_url, thumb_url

    hero_path = POST_IMAGES_DIR / f"{slug}-hero{ext}"
    hero_path.write_bytes(image_bytes)
    thumb_path = POST_IMAGES_DIR / f"{slug}-thumb.jpg"
    thumb_path.write_bytes(thumb_bytes)
    return (
        f"/static/post-images/{slug}-hero{ext}",
        f"/static/post-images/{slug}-thumb.jpg",
    )


def save_block_image(image_bytes: bytes, name: str, ext: str) -> str:
    """
    Save an image uploaded via the block editor.

    Returns:
        S3/MinIO URL or relative /static/... path.
    """
    if _USE_S3:
        ext_ct = "image/jpeg" if ext.lower() in {".jpg", ".jpeg"} else "image/png"
        return _upload_to_s3(image_bytes, f"post-images/block-{name}{ext}", ext_ct)

    img_path = POST_IMAGES_DIR / f"block-{name}{ext}"
    img_path.write_bytes(image_bytes)
    return f"/static/post-images/block-{name}{ext}"


def save_favicon(svg_bytes: bytes, save_name: str) -> str:
    """
    Save a favicon SVG and generate PNG variants at standard sizes.
    Uploads to S3/MinIO if configured, otherwise saves to local filesystem.

    Returns:
        Public URL of the saved SVG.
    """
    png_variants = _generate_favicon_pngs(svg_bytes, save_name)

    if _USE_S3:
        svg_url = _upload_to_s3(svg_bytes, f"favicons/{save_name}.svg", "image/svg+xml")
        for key, data in png_variants:
            _upload_to_s3(data, key, "image/png")
        return svg_url

    svg_path = FAVICON_DIR / f"{save_name}.svg"
    svg_path.write_bytes(svg_bytes)
    for key, data in png_variants:
        (FAVICON_DIR / Path(key).name).write_bytes(data)
    return f"/static/favicons/{save_name}.svg"


def _generate_favicon_pngs(svg_bytes: bytes, save_name: str) -> List[Tuple[str, bytes]]:
    """
    Convert SVG to PNG variants at standard favicon sizes.

    Returns:
        List of (s3_key, png_bytes) tuples. Empty list if cairosvg is unavailable.
    """
    if not _CAIROSVG:
        return []
    results = []
    for size in EXPECTED_FAVICON_SIZES:
        try:
            png_bytes = _cairosvg.svg2png(
                bytestring=svg_bytes,
                output_width=size,
                output_height=size,
            )
            results.append((f"favicons/{save_name}-{size}.png", png_bytes))
        except Exception:
            pass
    return results

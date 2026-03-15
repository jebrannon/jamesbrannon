"""Hero image upload handler — saves original and generates 1200×630 thumbnail."""
import io
import logging
import os
from pathlib import Path
from typing import Tuple

from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

# Storage location mirrors static/favicons/
POST_IMAGES_DIR = Path(__file__).parent.parent.parent / "static" / "post-images"
POST_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

THUMB_SIZE = (1200, 630)  # Standard OG image dimensions

_S3_BUCKET = os.getenv("S3_BUCKET", "")
_S3_BUCKET_REGION = os.getenv("S3_BUCKET_REGION", "eu-west-2")
_USE_S3 = bool(_S3_BUCKET)


def _upload_to_s3(data: bytes, key: str, content_type: str) -> str:
    """Upload bytes to S3 and return the public URL."""
    import boto3
    s3 = boto3.client("s3", region_name=_S3_BUCKET_REGION)
    s3.put_object(
        Bucket=_S3_BUCKET,
        Key=key,
        Body=data,
        ContentType=content_type,
    )
    return f"https://{_S3_BUCKET}.s3.{_S3_BUCKET_REGION}.amazonaws.com/{key}"


def save_hero_image(image_bytes: bytes, slug: str, ext: str) -> Tuple[str, str]:
    """
    Save the uploaded image and generate a 1200×630 JPEG thumbnail.

    Returns:
        (hero_url, thumbnail_url) — relative /static/... paths (local) or S3 URLs
    """
    thumb_buf = io.BytesIO()
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img = ImageOps.fit(img, THUMB_SIZE, Image.LANCZOS)
    img.save(thumb_buf, "JPEG", quality=85)
    thumb_bytes = thumb_buf.getvalue()

    if _USE_S3:
        ext_ct = "image/jpeg" if ext.lower() in {".jpg", ".jpeg"} else "image/png"
        hero_url = _upload_to_s3(
            image_bytes, f"post-images/{slug}-hero{ext}", ext_ct
        )
        thumb_url = _upload_to_s3(
            thumb_bytes, f"post-images/{slug}-thumb.jpg", "image/jpeg"
        )
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
        Relative /static/... URL (local) or S3 URL.
    """
    if _USE_S3:
        ext_ct = "image/jpeg" if ext.lower() in {".jpg", ".jpeg"} else "image/png"
        return _upload_to_s3(
            image_bytes, f"post-images/block-{name}{ext}", ext_ct
        )

    img_path = POST_IMAGES_DIR / f"block-{name}{ext}"
    img_path.write_bytes(image_bytes)
    return f"/static/post-images/block-{name}{ext}"

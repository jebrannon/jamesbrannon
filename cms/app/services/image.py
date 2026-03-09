"""Hero image upload handler — saves original and generates 1200×630 thumbnail."""
import io
import logging
from pathlib import Path
from typing import Tuple

from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

# Storage location mirrors static/favicons/
POST_IMAGES_DIR = Path(__file__).parent.parent.parent / "static" / "post-images"
POST_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

THUMB_SIZE = (1200, 630)  # Standard OG image dimensions


def save_hero_image(image_bytes: bytes, slug: str, ext: str) -> Tuple[str, str]:
    """
    Save the uploaded image and generate a 1200×630 JPEG thumbnail.

    Returns:
        (hero_url, thumbnail_url) — both relative /static/... paths
    """
    # Save original
    hero_path = POST_IMAGES_DIR / f"{slug}-hero{ext}"
    hero_path.write_bytes(image_bytes)

    # Generate thumbnail (crop-to-fit at THUMB_SIZE)
    thumb_path = POST_IMAGES_DIR / f"{slug}-thumb.jpg"
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img = ImageOps.fit(img, THUMB_SIZE, Image.LANCZOS)
    img.save(str(thumb_path), "JPEG", quality=85)

    return (
        f"/static/post-images/{slug}-hero{ext}",
        f"/static/post-images/{slug}-thumb.jpg",
    )

from fastapi import APIRouter

from ..db import get_setting

router = APIRouter(tags=["settings"])


@router.get("/settings/brand")
def get_brand_settings() -> dict:
    """Return site-wide brand settings (favicon URLs, social links)."""
    return get_setting("BRAND") or {}


@router.get("/settings/homepage")
def get_homepage_settings() -> dict:
    """Return homepage-specific content and SEO settings."""
    return get_setting("HOMEPAGE") or {}

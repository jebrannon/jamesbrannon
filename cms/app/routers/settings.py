from fastapi import APIRouter

from ..db import get_setting

router = APIRouter(tags=["settings"])


@router.get("/settings/brand")
def get_brand_settings() -> dict:
    """Return site-wide brand settings (favicon URLs, social links)."""
    return get_setting("BRAND") or {}


@router.get("/settings/seo")
def get_seo_settings() -> dict:
    """Return site-level SEO and Open Graph settings."""
    return get_setting("SEO") or {}


@router.get("/settings/profile")
def get_profile_settings() -> dict:
    """Return personal profile content (headline, tagline, summary)."""
    return get_setting("PROFILE") or {}

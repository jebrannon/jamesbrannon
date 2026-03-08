from fastapi import APIRouter

from ..constants import SETTINGS_BRAND, SETTINGS_PROFILE, SETTINGS_SEO
from ..db import get_setting

router = APIRouter(tags=["settings"])


@router.get("/settings/brand")
def get_brand_settings() -> dict:
    """Return site-wide brand settings (favicon URLs, social links).
    Returns an empty dict when no settings have been saved yet.
    """
    return get_setting(SETTINGS_BRAND) or {}


@router.get("/settings/seo")
def get_seo_settings() -> dict:
    """Return site-level SEO and Open Graph settings.
    Returns an empty dict when no settings have been saved yet.
    """
    return get_setting(SETTINGS_SEO) or {}


@router.get("/settings/profile")
def get_profile_settings() -> dict:
    """Return personal profile content (headline, tagline, summary).
    Returns an empty dict when no settings have been saved yet.
    """
    return get_setting(SETTINGS_PROFILE) or {}

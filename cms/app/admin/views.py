from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from starlette.datastructures import UploadFile
from starlette.requests import Request
from starlette_admin.fields import (
    BooleanField,
    EmailField,
    EnumField,
    FileField,
    StringField,
    TagsField,
    TextAreaField,
    URLField,
)
from starlette_admin.base import BaseModelView

from ..db import delete_content, get_content, get_setting, list_content, put_content, put_setting
from ..models import OGType, ThemeMode, ThemeStyle

# ── Static file storage for favicons ──────────────────────────────────────────

STATIC_DIR = Path(__file__).parent.parent.parent / "static"
FAVICON_DIR = STATIC_DIR / "favicons"
FAVICON_DIR.mkdir(parents=True, exist_ok=True)

try:
    import cairosvg as _cairosvg
    _CAIROSVG = True
except (ImportError, OSError):
    # OSError is raised when libcairo system library is not installed.
    # Install with: brew install cairo (macOS) or apt install libcairo2 (Linux).
    _CAIROSVG = False

# ── Shared field groups ────────────────────────────────────────────────────────

THEME_FIELDS = [
    EnumField("theme_mode", label="Mode", enum=ThemeMode, required=True),
    EnumField("theme_style", label="Style", enum=ThemeStyle, required=True),
]

SEO_FIELDS = [
    StringField(
        "seo_title", label="SEO Title", required=False,
        help_text="Overrides page title in search results (~60 chars)",
    ),
    TextAreaField(
        "seo_description", label="Meta Description", required=False,
        help_text="~155 chars — shown in search results and og:description",
    ),
    StringField(
        "og_image", label="OG Image URL", required=False,
        help_text="Absolute URL for social sharing image (1200x630 px recommended)",
    ),
    EnumField("og_type", label="OG Type", enum=OGType, required=False),
    StringField(
        "canonical_url", label="Canonical URL", required=False,
        help_text="Leave blank to use the page URL automatically",
    ),
    BooleanField("no_index", label="No Index (hide from search engines)"),
]


# ── Helpers ────────────────────────────────────────────────────────────────────

def _normalize(data: Dict) -> Dict:
    """Convert Enum instances to their string values for DynamoDB storage."""
    return {k: v.value if isinstance(v, Enum) else v for k, v in data.items()}


def _unpack_file(field_value: Any) -> Tuple[Optional[UploadFile], bool]:
    """
    starlette-admin FileField.parse_form_data returns (file, should_be_deleted).
    Handle both tuple and bare values defensively.
    """
    if isinstance(field_value, tuple):
        return field_value  # (UploadFile | None, bool)
    return field_value, False


def _convert_favicon(svg_bytes: bytes, save_name: str) -> None:
    """Convert SVG bytes to PNG variants at standard favicon sizes."""
    if not _CAIROSVG:
        return
    for size in [16, 32, 192, 512]:
        out = FAVICON_DIR / f"{save_name}-{size}.png"
        try:
            _cairosvg.svg2png(
                bytestring=svg_bytes,
                write_to=str(out),
                output_width=size,
                output_height=size,
            )
        except Exception:
            pass  # Skip silently if conversion fails for a particular size


# ── Content type views ─────────────────────────────────────────────────────────

class PostView(BaseModelView):
    identity = "post"
    name = "Post"
    label = "Blog Posts"
    pk_attr = "slug"
    fields = [
        StringField("slug", label="Slug", required=True,
                    help_text="URL-friendly, e.g. my-first-post"),
        StringField("title", label="Title", required=True),
        TextAreaField("body", label="Body (Markdown)", required=True),
        StringField("date", label="Date (ISO 8601)", required=False,
                    help_text="e.g. 2026-03-07T09:00:00"),
        BooleanField("published", label="Published"),
        TagsField("tags", label="Tags"),
        StringField("excerpt", label="Excerpt", required=False),
        *THEME_FIELDS,
        *SEO_FIELDS,
    ]

    async def count(self, request: Request, where=None) -> int:
        return len(list_content("POST"))

    async def find_all(
        self, request: Request, skip: int = 0, limit: int = 100,
        where=None, order_by=None
    ) -> Sequence[Any]:
        return list_content("POST")[skip: skip + limit]

    async def find_by_pk(self, request: Request, pk: Any) -> Any:
        item = get_content("POST", str(pk))
        if not item:
            raise ValueError(f"Post '{pk}' not found")
        return item

    async def create(self, request: Request, data: Dict[str, Any]) -> Any:
        put_content("POST", _normalize(data))
        return data

    async def edit(self, request: Request, pk: Any, data: Dict[str, Any]) -> Any:
        put_content("POST", _normalize(data))
        return data

    async def delete(self, request: Request, pks: List[Any]) -> Optional[int]:
        for pk in pks:
            delete_content("POST", str(pk))
        return len(pks)


class PageView(BaseModelView):
    identity = "page"
    name = "Page"
    label = "Pages"
    pk_attr = "slug"
    fields = [
        StringField("slug", label="Slug", required=True,
                    help_text="e.g. about"),
        StringField("title", label="Title", required=True),
        TextAreaField("body", label="Body (Markdown)", required=False),
        *THEME_FIELDS,
        *SEO_FIELDS,
    ]

    async def count(self, request: Request, where=None) -> int:
        return len(list_content("PAGE"))

    async def find_all(
        self, request: Request, skip: int = 0, limit: int = 100,
        where=None, order_by=None
    ) -> Sequence[Any]:
        return list_content("PAGE")[skip: skip + limit]

    async def find_by_pk(self, request: Request, pk: Any) -> Any:
        item = get_content("PAGE", str(pk))
        if not item:
            raise ValueError(f"Page '{pk}' not found")
        return item

    async def create(self, request: Request, data: Dict[str, Any]) -> Any:
        put_content("PAGE", _normalize(data))
        return data

    async def edit(self, request: Request, pk: Any, data: Dict[str, Any]) -> Any:
        put_content("PAGE", _normalize(data))
        return data

    async def delete(self, request: Request, pks: List[Any]) -> Optional[int]:
        for pk in pks:
            delete_content("PAGE", str(pk))
        return len(pks)


class PortfolioView(BaseModelView):
    identity = "portfolio"
    name = "Portfolio Item"
    label = "Portfolio"
    pk_attr = "slug"
    fields = [
        StringField("slug", label="Slug", required=True),
        StringField("title", label="Title", required=True),
        TextAreaField("body", label="Body (Markdown)", required=True),
        StringField("date", label="Date (ISO 8601)", required=False),
        BooleanField("featured", label="Featured on home page"),
        StringField("thumbnail_url", label="Thumbnail URL", required=False),
        TagsField("tags", label="Tags"),
        StringField("excerpt", label="Excerpt", required=False),
        *THEME_FIELDS,
        *SEO_FIELDS,
    ]

    async def count(self, request: Request, where=None) -> int:
        return len(list_content("PORTFOLIO"))

    async def find_all(
        self, request: Request, skip: int = 0, limit: int = 100,
        where=None, order_by=None
    ) -> Sequence[Any]:
        return list_content("PORTFOLIO")[skip: skip + limit]

    async def find_by_pk(self, request: Request, pk: Any) -> Any:
        item = get_content("PORTFOLIO", str(pk))
        if not item:
            raise ValueError(f"Portfolio item '{pk}' not found")
        return item

    async def create(self, request: Request, data: Dict[str, Any]) -> Any:
        put_content("PORTFOLIO", _normalize(data))
        return data

    async def edit(self, request: Request, pk: Any, data: Dict[str, Any]) -> Any:
        put_content("PORTFOLIO", _normalize(data))
        return data

    async def delete(self, request: Request, pks: List[Any]) -> Optional[int]:
        for pk in pks:
            delete_content("PORTFOLIO", str(pk))
        return len(pks)


# ── Singleton settings views ───────────────────────────────────────────────────

class BrandView(BaseModelView):
    """
    Singleton admin view for site-wide brand settings.
    Always shows exactly one row; can_create and can_delete are disabled.
    """
    identity = "brand"
    name = "Brand"
    label = "Brand Settings"
    pk_attr = "key"
    can_create = False
    can_delete = False

    SETTINGS_KEY = "BRAND"

    fields = [
        # Favicon uploads — SVG files are saved and converted to PNG variants
        FileField(
            "favicon_light",
            label="Favicon (Light Mode) — Upload SVG",
            help_text=(
                "Upload an SVG. PNGs at 16/32/192/512 px are generated automatically "
                "(requires libcairo; run: brew install cairo on macOS)."
            ),
            required=False,
            accept=".svg,image/svg+xml",
        ),
        FileField(
            "favicon_dark",
            label="Favicon (Dark Mode) — Upload SVG",
            required=False,
            accept=".svg,image/svg+xml",
        ),
        # URL display — excluded from forms, visible in list/detail only
        StringField(
            "favicon_light_url", label="Light Favicon URL",
            exclude_from_create=True, exclude_from_edit=True, required=False,
        ),
        StringField(
            "favicon_dark_url", label="Dark Favicon URL",
            exclude_from_create=True, exclude_from_edit=True, required=False,
        ),
        URLField("linkedin", label="LinkedIn URL", required=False),
        URLField("instagram", label="Instagram URL", required=False),
        EmailField("email", label="Contact Email", required=False),
    ]

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _defaults(self) -> Dict:
        return {
            "key": self.SETTINGS_KEY,
            "favicon_light_url": "",
            "favicon_dark_url": "",
            "linkedin": "",
            "instagram": "",
            "email": "",
        }

    def _with_key(self, item: Dict) -> Dict:
        item["key"] = self.SETTINGS_KEY
        return item

    async def _save_favicon(
        self, field_value: Any, save_name: str, existing_url: str
    ) -> str:
        """
        Process a FileField value: save the SVG and generate PNG variants.
        Returns the new URL if a file was uploaded, otherwise the existing URL.
        """
        file, should_delete = _unpack_file(field_value)
        if should_delete:
            return ""
        if file and hasattr(file, "read") and getattr(file, "filename", ""):
            content = await file.read()
            if content:
                svg_path = FAVICON_DIR / f"{save_name}.svg"
                svg_path.write_bytes(content)
                _convert_favicon(content, save_name)
                return f"/static/favicons/{save_name}.svg"
        return existing_url

    # ── BaseModelView interface ───────────────────────────────────────────────

    async def count(self, request: Request, where=None) -> int:
        return 1  # Singleton always has exactly one record

    async def find_all(
        self, request: Request, skip: int = 0, limit: int = 100,
        where=None, order_by=None
    ) -> Sequence[Any]:
        item = get_setting(self.SETTINGS_KEY) or {}
        return [self._with_key({**self._defaults(), **item})]

    async def find_by_pk(self, request: Request, pk: Any) -> Any:
        item = get_setting(self.SETTINGS_KEY) or {}
        return self._with_key({**self._defaults(), **item})

    async def create(self, request: Request, data: Dict[str, Any]) -> Any:
        existing = get_setting(self.SETTINGS_KEY) or {}
        data["favicon_light_url"] = await self._save_favicon(
            data.pop("favicon_light", None),
            "favicon-light",
            existing.get("favicon_light_url", ""),
        )
        data["favicon_dark_url"] = await self._save_favicon(
            data.pop("favicon_dark", None),
            "favicon-dark",
            existing.get("favicon_dark_url", ""),
        )
        data.pop("key", None)
        put_setting(self.SETTINGS_KEY, data)
        return data

    async def edit(self, request: Request, pk: Any, data: Dict[str, Any]) -> Any:
        existing = get_setting(self.SETTINGS_KEY) or {}
        data["favicon_light_url"] = await self._save_favicon(
            data.pop("favicon_light", None),
            "favicon-light",
            existing.get("favicon_light_url", ""),
        )
        data["favicon_dark_url"] = await self._save_favicon(
            data.pop("favicon_dark", None),
            "favicon-dark",
            existing.get("favicon_dark_url", ""),
        )
        data.pop("key", None)
        put_setting(self.SETTINGS_KEY, data)
        return data

    async def delete(self, request: Request, pks: List[Any]) -> Optional[int]:
        return 0  # Deletion disabled


class HomepageView(BaseModelView):
    """
    Singleton admin view for homepage content and SEO settings.
    """
    identity = "homepage"
    name = "Homepage"
    label = "Homepage Settings"
    pk_attr = "key"
    can_create = False
    can_delete = False

    SETTINGS_KEY = "HOMEPAGE"

    fields = [
        TextAreaField("tagline", label="Tagline", required=False,
                      help_text="Short headline shown on the homepage"),
        TextAreaField("bio", label="Bio / About Text", required=False),
        StringField("hero_image_url", label="Hero Image URL", required=False),
        StringField("cta_text", label="CTA Button Text", required=False,
                    help_text="e.g. View my work"),
        URLField("cta_url", label="CTA Button URL", required=False),
        *SEO_FIELDS,
    ]

    def _defaults(self) -> Dict:
        return {
            "key": self.SETTINGS_KEY,
            "tagline": "",
            "bio": "",
            "hero_image_url": "",
            "cta_text": "",
            "cta_url": "",
            "seo_title": "",
            "seo_description": "",
            "og_image": "",
            "og_type": "website",
            "canonical_url": "",
            "no_index": False,
        }

    def _with_key(self, item: Dict) -> Dict:
        item["key"] = self.SETTINGS_KEY
        return item

    async def count(self, request: Request, where=None) -> int:
        return 1

    async def find_all(
        self, request: Request, skip: int = 0, limit: int = 100,
        where=None, order_by=None
    ) -> Sequence[Any]:
        item = get_setting(self.SETTINGS_KEY) or {}
        return [self._with_key({**self._defaults(), **item})]

    async def find_by_pk(self, request: Request, pk: Any) -> Any:
        item = get_setting(self.SETTINGS_KEY) or {}
        return self._with_key({**self._defaults(), **item})

    async def create(self, request: Request, data: Dict[str, Any]) -> Any:
        data.pop("key", None)
        put_setting(self.SETTINGS_KEY, _normalize(data))
        return data

    async def edit(self, request: Request, pk: Any, data: Dict[str, Any]) -> Any:
        data.pop("key", None)
        put_setting(self.SETTINGS_KEY, _normalize(data))
        return data

    async def delete(self, request: Request, pks: List[Any]) -> Optional[int]:
        return 0

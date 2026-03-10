import json as _json
import re as _re
from enum import Enum
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Sequence, Tuple

import bleach as _bleach
from starlette.datastructures import UploadFile
from starlette.requests import Request
from starlette.responses import Response
from starlette.templating import Jinja2Templates
from starlette_admin.views import CustomView
from starlette_admin.fields import (
    BooleanField,
    CollectionField,
    EmailField,
    EnumField,
    FileField,
    IntegerField,
    ListField,
    StringField,
    TextAreaField,
    URLField,
)
from starlette_admin.base import BaseModelView

# ── Block editor helpers ───────────────────────────────────────────────────────

_ALLOWED_TAGS = ["p", "h2", "h3", "strong", "em", "ul", "ol", "li", "a", "br"]
_ALLOWED_ATTRS: Dict[str, List[str]] = {"a": ["href", "title", "target"]}


def _sanitize_blocks(raw_json: str) -> str:
    """Parse a JSON blocks string, sanitise each block's text and media, return sanitised JSON."""
    try:
        blocks = _json.loads(raw_json)
    except (_json.JSONDecodeError, ValueError):
        return "[]"
    if not isinstance(blocks, list):
        return "[]"
    for block in blocks:
        # Sanitise block text
        if isinstance(block.get("text"), str):
            cleaned = _bleach.clean(
                block["text"], tags=_ALLOWED_TAGS, attributes=_ALLOWED_ATTRS, strip=True
            )
            block["text"] = cleaned if cleaned.strip() else None

        # Normalise media: null → [], dict (legacy) → [dict], list kept as-is
        media = block.get("media")
        if media is None:
            media = []
        elif isinstance(media, dict):
            media = [media]  # backward-compat: upgrade single-object to array
        elif not isinstance(media, list):
            media = []
        # Sanitise each media item's plain-text fields
        for item in media:
            if not isinstance(item, dict):
                continue
            for field in ("alt", "caption"):
                if isinstance(item.get(field), str):
                    item[field] = _bleach.clean(item[field], tags=[], attributes={}, strip=True)
        block["media"] = media

    return _json.dumps(blocks)


def _blocks_as_plain_text(blocks_json: Any) -> str:
    """Extract plain text from all blocks for Ollama excerpt generation."""
    try:
        blocks = _json.loads(blocks_json) if isinstance(blocks_json, str) else (blocks_json or [])
    except Exception:
        return ""
    parts = []
    for b in blocks:
        txt = b.get("text") or ""
        txt = _re.sub(r"<[^>]+>", " ", txt)
        txt = _re.sub(r"\s+", " ", txt).strip()
        if txt:
            parts.append(txt)
    return " ".join(parts)


class BlocksField(StringField):
    """Structured block editor — text + optional media, repeatable."""

    def __post_init__(self) -> None:
        super().__post_init__()
        self.form_template = "forms/blocks.html"
        self.exclude_from_list = True

    async def parse_form_data(self, request: Request, form_data, action) -> str:
        raw = form_data.get(self.name, "[]") or "[]"
        return _sanitize_blocks(raw)

    async def serialize_value(self, request: Request, value, action) -> str:
        if isinstance(value, list):
            return _json.dumps(value)
        return value or "[]"


class RichTextField(StringField):
    """Single contenteditable rich-text field with a 6-button formatting toolbar.

    Renders the same toolbar/contenteditable UI as the block editor text area.
    Sanitises HTML through bleach on save, keeping the same allowed-tag whitelist.
    """

    def __post_init__(self) -> None:
        super().__post_init__()
        self.form_template = "forms/rich_text.html"
        self.exclude_from_list = True

    async def parse_form_data(self, request: Request, form_data, action) -> str:
        # Use self.id (not self.name) — starlette-admin sets field.id to the
        # full dotted path (e.g. "strengths.items.0.description") for nested fields.
        raw = form_data.get(self.id, "") or ""
        return _bleach.clean(raw, tags=_ALLOWED_TAGS, attributes=_ALLOWED_ATTRS, strip=True)

    async def serialize_value(self, request: Request, value, action) -> str:
        return value or ""


class FieldsetCollectionField(CollectionField):
    """CollectionField that renders its label as a <legend> inside the <fieldset>."""
    label_template: str = "forms/_empty_label.html"
    form_template: str = "forms/collection_fieldset.html"

    def __init__(self, name: str, fields, label: str = "", required: bool = False) -> None:
        super().__init__(name=name, fields=fields, required=required)
        if label:
            self.label = label


from ..constants import (
    CONTENT_CATEGORY, CONTENT_PAGE, CONTENT_POST,
    SETTINGS_BLOG, SETTINGS_BRAND, SETTINGS_LAST_UPDATED, SETTINGS_PROFILE, SETTINGS_SEO,
)
from ..db import delete_content, get_content, get_setting, list_content, put_content, put_setting, touch_last_updated
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
    EnumField("theme_mode", label="Mode", enum=ThemeMode, required=True,
              exclude_from_list=True),
    EnumField("theme_style", label="Style", enum=ThemeStyle, required=True,
              exclude_from_list=True),
]

SEO_FIELDS = [
    StringField(
        "seo_title", label="SEO Title", required=False,
        help_text="Overrides page title in search results (~60 chars)",
        exclude_from_list=True,
    ),
    TextAreaField(
        "seo_description", label="Meta Description", required=False,
        help_text="~155 chars — shown in search results and og:description",
        exclude_from_list=True,
    ),
    StringField(
        "og_image", label="OG Image URL", required=False,
        help_text="Absolute URL for social sharing image (1200x630 px recommended)",
        exclude_from_list=True,
    ),
    EnumField("og_type", label="OG Type", enum=OGType, required=False,
              exclude_from_list=True),
    StringField(
        "canonical_url", label="Canonical URL", required=False,
        help_text="Leave blank to use the page URL automatically",
        exclude_from_list=True,
    ),
    BooleanField("no_index", label="No Index (hide from search engines)",
                 exclude_from_list=True),
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


def _as_obj(d: Optional[Dict]) -> Optional[SimpleNamespace]:
    """
    Recursively wrap a plain dict (and nested dicts/lists-of-dicts) in
    SimpleNamespace so starlette-admin can access fields via getattr().

    Deep wrapping is required for CollectionField: starlette-admin calls
    getattr(value, field.name) on the value returned for each nested field.
    A plain dict fails for keys that shadow built-in dict methods (e.g. "items"
    returns dict.items rather than raising AttributeError). SimpleNamespace
    ensures attribute access always reads the stored value.

    NOTE: This is a workaround for starlette-admin's internal use of getattr()
    on objects returned by find_by_pk, create, and edit. Test _as_obj_returns_
    namespace_with_attributes in test_admin_views.py guards against regressions
    if starlette-admin changes this behaviour in a future version.
    """
    if d is None:
        return None
    wrapped = {}
    for k, v in d.items():
        if isinstance(v, dict):
            wrapped[k] = _as_obj(v)
        elif isinstance(v, list):
            wrapped[k] = [_as_obj(i) if isinstance(i, dict) else i for i in v]
        else:
            wrapped[k] = v
    return SimpleNamespace(**wrapped)


EXPECTED_FAVICON_SIZES = [16, 32, 192, 512]


def _convert_favicon(svg_bytes: bytes, save_name: str) -> None:
    """Convert SVG bytes to PNG variants at standard favicon sizes."""
    if not _CAIROSVG:
        return
    for size in EXPECTED_FAVICON_SIZES:
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


# ── Dashboard ──────────────────────────────────────────────────────────────────

class DashboardView(CustomView):
    """Custom admin home page — last-updated timestamp + dashboard modules."""

    def __init__(self):
        super().__init__(
            label="Dashboard",
            icon="fa fa-home",
            path="/",
            template_path="dashboard.html",
            name="dashboard",
            add_to_menu=False,
        )

    async def render(self, request: Request, templates: Jinja2Templates) -> Response:
        posts = list_content(CONTENT_POST)
        published = sorted(
            [p for p in posts if p.get("published")],
            key=lambda x: x.get("date", ""),
            reverse=True,
        )
        latest_post = published[0] if published else None
        last_updated = (get_setting(SETTINGS_LAST_UPDATED) or {}).get("updated_at")
        return templates.TemplateResponse(
            request=request,
            name="dashboard.html",
            context={
                "title": "Dashboard",
                "latest_post": latest_post,
                "last_updated": last_updated,
            },
        )


# ── Content base view ──────────────────────────────────────────────────────────

class ContentView(BaseModelView):
    """
    Shared CRUD implementation for all content types (Post, Page, Portfolio).
    Subclasses must set CONTENT_TYPE to the DynamoDB content type string.
    """
    CONTENT_TYPE: str  # must be set in subclass

    async def count(self, request: Request, where=None) -> int:
        return len(list_content(self.CONTENT_TYPE))

    async def find_all(
        self, request: Request, skip: int = 0, limit: int = 100,
        where=None, order_by=None
    ) -> Sequence[Any]:
        return [_as_obj(d) for d in list_content(self.CONTENT_TYPE)[skip: skip + limit]]

    async def find_by_pk(self, request: Request, pk: Any) -> Any:
        item = get_content(self.CONTENT_TYPE, str(pk))
        if not item:
            raise ValueError(f"{self.name} '{pk}' not found")
        return _as_obj(item)

    async def create(self, request: Request, data: Dict[str, Any]) -> Any:
        # starlette-admin strips pk_attr from data before calling create().
        # Re-read it from the cached request form (starlette caches form data).
        if self.pk_attr not in data:
            form = await request.form()
            data[self.pk_attr] = str(form.get(self.pk_attr, ""))
        normalised = _normalize(data)
        put_content(self.CONTENT_TYPE, normalised)
        touch_last_updated()
        return _as_obj(normalised)

    async def edit(self, request: Request, pk: Any, data: Dict[str, Any]) -> Any:
        normalised = _normalize(data)
        normalised.setdefault("slug", str(pk))
        put_content(self.CONTENT_TYPE, normalised)
        touch_last_updated()
        return _as_obj(normalised)

    async def delete(self, request: Request, pks: List[Any]) -> Optional[int]:
        for pk in pks:
            delete_content(self.CONTENT_TYPE, str(pk))
        touch_last_updated()
        return len(pks)


# ── Singleton base view ────────────────────────────────────────────────────────

class SingletonView(BaseModelView):
    """
    Shared CRUD implementation for singleton settings records (SEO, Profile, …).
    Subclasses must set SETTINGS_KEY and implement _defaults().
    """
    SETTINGS_KEY: str  # must be set in subclass
    pk_attr = "key"
    list_template = "singleton_redirect.html"
    edit_template = "singleton_edit.html"

    def can_create(self, request: Request) -> bool:
        return False

    def can_delete(self, request: Request) -> bool:
        return False

    def _defaults(self) -> Dict:
        raise NotImplementedError

    def _with_key(self, item: Dict) -> Dict:
        item["key"] = self.SETTINGS_KEY
        return item

    async def count(self, request: Request, where=None) -> int:
        return 1  # Singleton always has exactly one record

    async def find_all(
        self, request: Request, skip: int = 0, limit: int = 100,
        where=None, order_by=None
    ) -> Sequence[Any]:
        item = get_setting(self.SETTINGS_KEY) or {}
        return [_as_obj(self._with_key({**self._defaults(), **item}))]

    async def find_by_pk(self, request: Request, pk: Any) -> Any:
        item = get_setting(self.SETTINGS_KEY) or {}
        return _as_obj(self._with_key({**self._defaults(), **item}))

    async def create(self, request: Request, data: Dict[str, Any]) -> Any:
        data.pop("key", None)
        normalised = _normalize(data)
        put_setting(self.SETTINGS_KEY, normalised)
        touch_last_updated()
        normalised["key"] = self.SETTINGS_KEY
        return _as_obj(normalised)

    async def edit(self, request: Request, pk: Any, data: Dict[str, Any]) -> Any:
        data.pop("key", None)
        normalised = _normalize(data)
        put_setting(self.SETTINGS_KEY, normalised)
        touch_last_updated()
        normalised["key"] = self.SETTINGS_KEY
        return _as_obj(normalised)

    async def delete(self, request: Request, pks: List[Any]) -> Optional[int]:
        return 0  # Deletion disabled


# ── Content type views ─────────────────────────────────────────────────────────

class PageSelectField(StringField):
    """StringField rendered as a dynamic <select> populated from /api/pages."""
    def __post_init__(self) -> None:
        super().__post_init__()
        self.form_template = "forms/page_select.html"


class CategorySelectField(StringField):
    """StringField rendered as a dynamic <select> populated from /api/categories."""
    def __post_init__(self) -> None:
        super().__post_init__()
        self.form_template = "forms/category_select.html"


class SlugAutoFillField(StringField):
    """Slug field that auto-fills from the title (posts) or name (categories) on create."""
    def __post_init__(self) -> None:
        super().__post_init__()
        self.form_template = "forms/slug_autofill.html"


class PostView(ContentView):
    CONTENT_TYPE = CONTENT_POST
    identity = "post"
    name = "Post"
    label = "Posts"
    pk_attr = "slug"
    form_include_pk = True
    fields = [
        StringField("title", label="Title", required=True),
        SlugAutoFillField("slug", label="Slug", required=True,
                          help_text="Auto-filled from title — override to set a custom URL"),
        BlocksField("blocks", label="Content Blocks", required=False),
        StringField("date", label="Date (ISO 8601)", required=False,
                    help_text="e.g. 2026-03-07T09:00:00"),
        TextAreaField("excerpt", label="Summary / Excerpt", required=False,
                      help_text="Leave blank to auto-generate from content on save",
                      exclude_from_list=True),
        FileField(
            "hero_image",
            label="Hero Image",
            required=False,
            help_text=(
                "Uploaded image is saved as-is; a 1200×630 JPEG thumbnail is "
                "auto-generated for SEO and feed display."
            ),
            accept="image/*",
            exclude_from_list=True,
        ),
        # URL display fields — excluded from forms and list view; visible in detail only
        StringField("hero_image_url", label="Hero Image URL",
                    exclude_from_create=True, exclude_from_edit=True,
                    exclude_from_list=True, required=False),
        StringField("hero_thumbnail_url", label="Hero Thumbnail URL",
                    exclude_from_create=True, exclude_from_edit=True,
                    exclude_from_list=True, required=False),
        BooleanField("published", label="Published"),
        CategorySelectField("category", label="Category", required=False,
                            help_text="Assign this post to a category"),
        *THEME_FIELDS,
        *SEO_FIELDS,
    ]

    async def _save_hero(
        self, field_value: Any, slug: str, existing_hero_url: str, existing_thumb_url: str
    ) -> Tuple[str, str]:
        """
        Process the hero_image FileField value.
        Returns (hero_url, thumbnail_url) — unchanged if no new file was uploaded.
        """
        from ..services.image import save_hero_image

        file, should_delete = _unpack_file(field_value)
        if should_delete:
            return "", ""
        if file and hasattr(file, "read") and getattr(file, "filename", ""):
            content = await file.read()
            if content:
                ext = Path(file.filename).suffix.lower() or ".jpg"
                return save_hero_image(content, slug, ext)
        return existing_hero_url, existing_thumb_url

    async def _enrich(self, data: Dict[str, Any], slug: str) -> Dict[str, Any]:
        """
        1. Process hero image upload → set hero_image_url + hero_thumbnail_url
        2. Auto-generate excerpt via Ollama if blank
        3. Pre-fill seo_description from excerpt, seo_title from title, og_image from thumbnail
           — only when those fields are currently empty so manual overrides are preserved
        """
        from ..services.llm import generate_excerpt as _gen

        # ── Hero image ────────────────────────────────────────────────────────
        existing = get_content(self.CONTENT_TYPE, slug) or {}
        hero_url, thumb_url = await self._save_hero(
            data.pop("hero_image", None),
            slug,
            existing.get("hero_image_url", ""),
            existing.get("hero_thumbnail_url", ""),
        )
        data["hero_image_url"] = hero_url
        data["hero_thumbnail_url"] = thumb_url

        # ── Auto-excerpt ──────────────────────────────────────────────────────
        if not data.get("excerpt"):
            data["excerpt"] = await _gen(
                title=data.get("title", ""),
                body=_blocks_as_plain_text(data.get("blocks", "[]")),
            )

        # ── SEO pre-fills ─────────────────────────────────────────────────────
        if not data.get("seo_description") and data.get("excerpt"):
            data["seo_description"] = data["excerpt"]
        if not data.get("seo_title") and data.get("title"):
            data["seo_title"] = data["title"]
        if not data.get("og_image") and thumb_url:
            data["og_image"] = thumb_url

        return data

    async def create(self, request: Request, data: Dict[str, Any]) -> Any:
        if self.pk_attr not in data:
            form = await request.form()
            data[self.pk_attr] = str(form.get(self.pk_attr, ""))
        slug = data.get(self.pk_attr, "")
        data = await self._enrich(data, slug)
        normalised = _normalize(data)
        put_content(self.CONTENT_TYPE, normalised)
        touch_last_updated()
        return _as_obj(normalised)

    async def edit(self, request: Request, pk: Any, data: Dict[str, Any]) -> Any:
        data = await self._enrich(data, str(pk))
        normalised = _normalize(data)
        normalised.setdefault("slug", str(pk))
        put_content(self.CONTENT_TYPE, normalised)
        touch_last_updated()
        return _as_obj(normalised)


class PageView(ContentView):
    CONTENT_TYPE = CONTENT_PAGE
    identity = "page"
    name = "Page"
    label = "Pages"
    pk_attr = "slug"
    form_include_pk = True
    fields = [
        StringField("slug", label="Slug", required=True,
                    help_text="e.g. about"),
        StringField("title", label="Title", required=True),
        BlocksField("blocks", label="Content Blocks", required=False),
        BooleanField("published", label="Published"),
        *THEME_FIELDS,
        *SEO_FIELDS,
    ]


class CategoryView(ContentView):
    """CRUD view for blog categories."""
    CONTENT_TYPE = CONTENT_CATEGORY
    identity = "category"
    name = "Category"
    label = "Categories"
    pk_attr = "slug"
    form_include_pk = True
    fields = [
        StringField("name", label="Name", required=True),
        SlugAutoFillField("slug", label="Slug", required=True,
                          help_text="Auto-filled from name — override to set a custom URL"),
        StringField("page_headline", label="Landing Page Headline", required=False,
                    help_text="Displayed at the top of the category listing page",
                    exclude_from_list=True),
        IntegerField("max_items", label="Max Items Per Page", required=False,
                     help_text="Pagination limit for the category landing page (default: 10)",
                     exclude_from_list=True),
        *THEME_FIELDS,
        *SEO_FIELDS,
    ]


# ── Singleton settings views ───────────────────────────────────────────────────

class BlogSettingsView(SingletonView):
    """Singleton admin view for blog landing page settings."""
    SETTINGS_KEY = SETTINGS_BLOG
    identity = "blog-settings"
    name = "Blog Settings"
    label = "Settings"
    fields = [
        StringField("page_headline", label="Blog Page Headline", required=False,
                    help_text="Heading shown at the top of the /blog landing page"),
    ]

    def _defaults(self) -> Dict:
        return {"key": self.SETTINGS_KEY, "page_headline": ""}


class BrandView(SingletonView):
    """
    Singleton admin view for site-wide brand settings.
    Overrides create/edit to handle SVG favicon uploads.
    """
    SETTINGS_KEY = SETTINGS_BRAND
    identity = "brand"
    name = "Brand"
    label = "Brand + Comms"
    edit_template = "brand_edit.html"

    fields = [
        # Favicon uploads — SVG files are saved and converted to PNG variants
        FileField(
            "favicon_light",
            label="Favicon — Light Mode",
            help_text=(
                "Upload an SVG. PNGs are auto-generated at 16 × 16, 32 × 32, "
                "192 × 192 and 512 × 512 px. "
                "Requires libcairo — brew install cairo (macOS) or "
                "apt install libcairo2 (Linux)."
            ),
            required=False,
            accept=".svg,image/svg+xml",
        ),
        FileField(
            "favicon_dark",
            label="Favicon — Dark Mode",
            help_text=(
                "Shown when the visitor's device is in dark mode. "
                "Falls back to the light favicon if not set. "
                "Same SVG → PNG conversion applies."
            ),
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
        StringField("linkedin_text", label="LinkedIn Display Text", required=False,
                    help_text="Text shown as the clickable link, e.g. /in/jamesbrannon"),
        URLField("instagram", label="Instagram URL", required=False),
        StringField("instagram_text", label="Instagram Display Text", required=False,
                    help_text="Text shown as the clickable link, e.g. @jamesbrannon"),
        EmailField("email", label="Email Address", required=False),
        StringField("email_text", label="Email Display Text", required=False,
                    help_text="Text shown as the clickable link, e.g. me@jamesbrannon.co.uk"),
    ]

    def _defaults(self) -> Dict:
        return {
            "key": self.SETTINGS_KEY,
            "favicon_light_url": "",
            "favicon_dark_url": "",
            "linkedin": "",
            "linkedin_text": "",
            "instagram": "",
            "instagram_text": "",
            "email": "",
            "email_text": "",
        }

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
        touch_last_updated()
        data["key"] = self.SETTINGS_KEY
        return _as_obj(data)

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
        touch_last_updated()
        data["key"] = self.SETTINGS_KEY
        return _as_obj(data)


class SeoView(SingletonView):
    """Singleton admin view for site-level SEO and Open Graph settings."""
    SETTINGS_KEY = SETTINGS_SEO
    identity = "seo"
    name = "SEO"
    label = "SEO Metadata"
    fields = [*SEO_FIELDS]

    def _defaults(self) -> Dict:
        return {
            "key": self.SETTINGS_KEY,
            "seo_title": "",
            "seo_description": "",
            "og_image": "",
            "og_type": "website",
            "canonical_url": "",
            "no_index": False,
        }


class ProfileView(SingletonView):
    """Singleton admin view for homepage overview content."""
    SETTINGS_KEY = SETTINGS_PROFILE
    identity = "profile"
    name = "Overview"
    label = "Overview"
    fields = [
        # ── Personal intro ────────────────────────────────────────────────
        StringField("headline", label="Headline", required=False,
                    help_text="e.g. Product designer & frontend developer"),
        StringField("tagline", label="Tagline", required=False,
                    help_text="Short strapline shown beneath the headline"),
        RichTextField("summary", label="Summary", required=False,
                      help_text="A few sentences about you — shown on the landing page"),

        # ── Blog fieldset ─────────────────────────────────────────────────
        FieldsetCollectionField("blog", label="Blog", fields=[
            StringField("headline", label="Section Headline", required=False,
                        help_text="Heading shown above the blog feed on the homepage"),
            StringField("category", label="Category (tag filter)", required=False,
                        help_text="Filter posts by tag e.g. 'thoughts'. Leave blank to show all."),
            IntegerField("limit", label="Max Items", required=False,
                         help_text="Maximum number of posts to display (default: 3)"),
        ]),

        # ── Strengths fieldset ────────────────────────────────────────────
        FieldsetCollectionField("strengths", label="Strengths", fields=[
            StringField("headline", label="Section Headline", required=False),
            ListField(CollectionField("items", fields=[
                StringField("name", label="Name", required=True),
                RichTextField("description", label="Description", required=False),
            ])),
        ]),

        # ── Experience fieldset ───────────────────────────────────────────
        FieldsetCollectionField("experience", label="Experience", fields=[
            StringField("headline", label="Section Headline", required=False),
            ListField(CollectionField("items", fields=[
                StringField("job_title", label="Job Title", required=True),
                PageSelectField("page_link", label="Page Link", required=False,
                                help_text="Link to a page in this CMS"),
                StringField("company", label="Company", required=False),
                StringField("dates", label="Dates", required=False,
                            help_text="e.g. 2011\u20132014"),
                RichTextField("summary", label="Summary", required=False),
            ])),
        ]),
    ]

    def _defaults(self) -> Dict:
        return {
            "key": self.SETTINGS_KEY,
            "headline": "",
            "tagline": "",
            "summary": "",
            "blog": {"headline": "", "category": "", "limit": 3},
            "strengths": {"headline": "", "items": []},
            "experience": {"headline": "", "items": []},
        }

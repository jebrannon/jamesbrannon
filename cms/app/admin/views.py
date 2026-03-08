from enum import Enum
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Sequence, Tuple

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
    TagsField,
    TextAreaField,
    TinyMCEEditorField,
    URLField,
)
from starlette_admin.base import BaseModelView

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
        TextAreaField("body", label="Body (Markdown)", required=True),
        StringField("date", label="Date (ISO 8601)", required=False,
                    help_text="e.g. 2026-03-07T09:00:00"),
        BooleanField("published", label="Published"),
        CategorySelectField("category", label="Category", required=False,
                            help_text="Assign this post to a category"),
        TagsField("tags", label="Tags"),
        StringField("excerpt", label="Excerpt", required=False),
        *THEME_FIELDS,
        *SEO_FIELDS,
    ]


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
        TextAreaField("body", label="Body (Markdown)", required=False),
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
                    help_text="Displayed at the top of the category listing page"),
        IntegerField("max_items", label="Max Items Per Page", required=False,
                     help_text="Pagination limit for the category landing page (default: 10)"),
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
        TextAreaField("summary", label="Summary", required=False,
                      help_text="A few sentences about you — shown on the landing page"),

        # ── Blog fieldset ─────────────────────────────────────────────────
        CollectionField("blog", fields=[
            StringField("headline", label="Section Headline", required=False,
                        help_text="Heading shown above the blog feed on the homepage"),
            StringField("category", label="Category (tag filter)", required=False,
                        help_text="Filter posts by tag e.g. 'thoughts'. Leave blank to show all."),
            IntegerField("limit", label="Max Items", required=False,
                         help_text="Maximum number of posts to display (default: 3)"),
        ]),

        # ── Strengths fieldset ────────────────────────────────────────────
        CollectionField("strengths", fields=[
            StringField("headline", label="Section Headline", required=False),
            ListField(CollectionField("items", fields=[
                StringField("name", label="Name", required=True),
                TextAreaField("description", label="Description", required=False),
            ])),
        ]),

        # ── Experience fieldset ───────────────────────────────────────────
        CollectionField("experience", fields=[
            StringField("headline", label="Section Headline", required=False),
            ListField(CollectionField("items", fields=[
                StringField("job_title", label="Job Title", required=True),
                PageSelectField("page_link", label="Page Link", required=False,
                                help_text="Link to a page in this CMS"),
                StringField("company", label="Company", required=False),
                StringField("dates", label="Dates", required=False,
                            help_text="e.g. 2011\u20132014"),
                TinyMCEEditorField("summary", label="Summary", required=False),
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

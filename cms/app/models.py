import json as _json
import re
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class ThemeMode(str, Enum):
    dark = "dark"
    light = "light"


class ThemeStyle(str, Enum):
    professional = "professional"
    thoughts = "thoughts"


class OGType(str, Enum):
    website = "website"
    article = "article"
    profile = "profile"


_SLUG_RE = re.compile(r'^[a-z0-9][a-z0-9-]*$')


class SEOMixin(BaseModel):
    """SEO and Open Graph fields — mixed into all content types and settings."""
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    og_image: Optional[str] = None
    canonical_url: Optional[str] = None
    no_index: bool = False


class ContentBase(SEOMixin):
    """Base for all CMS content records — carries theme + SEO fields."""
    theme_mode: ThemeMode = ThemeMode.dark
    theme_style: ThemeStyle = ThemeStyle.professional


class Post(ContentBase):
    og_type: OGType = OGType.article  # posts default to article, not website
    slug: str = Field(min_length=1)
    title: str = Field(min_length=1)
    blocks: List[Dict[str, Any]] = Field(default_factory=list)
    date: Optional[str] = None  # ISO 8601 string
    published: bool = False
    category: Optional[str] = None  # stores category slug
    excerpt: Optional[str] = None
    hero_image_url: Optional[str] = None     # original upload URL
    hero_thumbnail_url: Optional[str] = None  # 1200×630 JPEG thumbnail URL

    @field_validator("slug")
    @classmethod
    def slug_must_be_url_safe(cls, v: str) -> str:
        if not _SLUG_RE.match(v):
            raise ValueError("slug must contain only lowercase letters, digits, and hyphens")
        return v

    @field_validator("blocks", mode="before")
    @classmethod
    def _parse_blocks(cls, v: Any) -> List[Dict[str, Any]]:
        if v is None:
            return []
        if isinstance(v, str):
            try:
                return _json.loads(v)
            except (_json.JSONDecodeError, ValueError):
                return []
        return v if isinstance(v, list) else []


class Category(ContentBase):
    """A blog category — powers future category landing pages."""
    slug: str = Field(min_length=1)
    name: str = Field(min_length=1)
    page_headline: Optional[str] = None
    max_items: int = 10  # pagination limit for the category landing page

    @field_validator("slug")
    @classmethod
    def slug_must_be_url_safe(cls, v: str) -> str:
        if not _SLUG_RE.match(v):
            raise ValueError("slug must contain only lowercase letters, digits, and hyphens")
        return v


class Page(ContentBase):
    slug: str = Field(min_length=1)
    title: str = Field(min_length=1)
    blocks: List[Dict[str, Any]] = Field(default_factory=list)
    published: bool = False

    @field_validator("slug")
    @classmethod
    def slug_must_be_url_safe(cls, v: str) -> str:
        if not _SLUG_RE.match(v):
            raise ValueError("slug must contain only lowercase letters, digits, and hyphens")
        return v

    @field_validator("blocks", mode="before")
    @classmethod
    def _parse_blocks(cls, v: Any) -> List[Dict[str, Any]]:
        if v is None:
            return []
        if isinstance(v, str):
            try:
                return _json.loads(v)
            except (_json.JSONDecodeError, ValueError):
                return []
        return v if isinstance(v, list) else []


class BlogPageSettings(BaseModel):
    """Settings for the blog landing page (/blog)."""
    page_headline: Optional[str] = None


class BrandSettings(BaseModel):
    """Site-wide brand identity — logo, favicon URL, social links and display text."""
    display_name: Optional[str] = None
    role_title: Optional[str] = None
    logo_url: str = ""
    logo_dark_mode: bool = False
    favicon_url: str = ""
    favicon_dark_mode: bool = False
    linkedin: Optional[str] = None
    linkedin_text: Optional[str] = None
    instagram: Optional[str] = None
    instagram_text: Optional[str] = None
    email: Optional[str] = None
    email_text: Optional[str] = None


class SeoSettings(BaseModel):
    """Site-level SEO and Open Graph defaults."""
    site_name: Optional[str] = None        # brand name — used as og:site_name
    seo_title: Optional[str] = None        # default <title> for homepage and unoverridden pages
    seo_description: Optional[str] = None  # fallback meta description
    og_image: Optional[str] = None         # fallback social image


class BlogSettings(BaseModel):
    """Blog feed settings for the homepage."""
    headline: Optional[str] = None
    category: Optional[str] = None  # maps to ?tag= filter on /api/posts
    limit: int = 3


class StrengthItem(BaseModel):
    """A single professional strength entry."""
    name: str
    description: Optional[str] = None


class StrengthsSection(BaseModel):
    """Strengths fieldset — headline + list of items."""
    headline: Optional[str] = None
    items: List[StrengthItem] = Field(default_factory=list)


class ExperienceItem(BaseModel):
    """A single work experience entry."""
    job_title: str
    page_link: Optional[str] = None   # stores page slug
    company: Optional[str] = None
    dates: Optional[str] = None       # free text e.g. "2011–2014"
    summary: Optional[str] = None     # HTML from TinyMCE


class ExperienceSection(BaseModel):
    """Experience fieldset — headline + list of items."""
    headline: Optional[str] = None
    items: List[ExperienceItem] = Field(default_factory=list)


class ProfileSettings(BaseModel):
    """Personal profile content — powers the landing page."""
    headline: Optional[str] = None
    tagline: Optional[str] = None
    summary: Optional[str] = None
    blog: Optional[BlogSettings] = None
    strengths: Optional[StrengthsSection] = None
    experience: Optional[ExperienceSection] = None

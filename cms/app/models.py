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
    og_type: OGType = OGType.website
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
    body: str
    date: Optional[str] = None  # ISO 8601 string
    published: bool = False
    tags: List[str] = Field(default_factory=list)
    excerpt: Optional[str] = None

    @field_validator("slug")
    @classmethod
    def slug_must_be_url_safe(cls, v: str) -> str:
        if not _SLUG_RE.match(v):
            raise ValueError("slug must contain only lowercase letters, digits, and hyphens")
        return v


class Page(ContentBase):
    slug: str = Field(min_length=1)
    title: str = Field(min_length=1)
    body: Optional[str] = None
    sections: List[Dict[str, Any]] = Field(default_factory=list)

    @field_validator("slug")
    @classmethod
    def slug_must_be_url_safe(cls, v: str) -> str:
        if not _SLUG_RE.match(v):
            raise ValueError("slug must contain only lowercase letters, digits, and hyphens")
        return v


class PortfolioItem(ContentBase):
    slug: str = Field(min_length=1)
    title: str = Field(min_length=1)
    body: str
    tags: List[str] = Field(default_factory=list)
    featured: bool = False
    thumbnail_url: str = ""
    date: Optional[str] = None
    excerpt: Optional[str] = None

    @field_validator("slug")
    @classmethod
    def slug_must_be_url_safe(cls, v: str) -> str:
        if not _SLUG_RE.match(v):
            raise ValueError("slug must contain only lowercase letters, digits, and hyphens")
        return v


class BrandSettings(BaseModel):
    """Site-wide brand identity — favicon URLs, social links and display text."""
    favicon_light_url: str = ""
    favicon_dark_url: str = ""
    linkedin: Optional[str] = None
    linkedin_text: Optional[str] = None
    instagram: Optional[str] = None
    instagram_text: Optional[str] = None
    email: Optional[str] = None
    email_text: Optional[str] = None


class SeoSettings(SEOMixin):
    """Site-level SEO and Open Graph settings."""
    pass


class BlogSettings(BaseModel):
    """Blog feed settings for the homepage."""
    headline: Optional[str] = None
    category: Optional[str] = None  # maps to ?tag= filter on /api/posts
    limit: int = 3


class StrengthItem(BaseModel):
    """A single professional strength entry."""
    name: str
    description: Optional[str] = None


class ProfileSettings(BaseModel):
    """Personal profile content — powers the landing page."""
    headline: Optional[str] = None
    tagline: Optional[str] = None
    summary: Optional[str] = None
    blog: Optional[BlogSettings] = None
    strengths_headline: Optional[str] = None
    strengths: List[StrengthItem] = Field(default_factory=list)

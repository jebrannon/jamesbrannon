from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


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
    slug: str
    title: str
    body: str
    date: Optional[str] = None  # ISO 8601 string
    published: bool = False
    tags: List[str] = Field(default_factory=list)
    excerpt: Optional[str] = None


class Page(ContentBase):
    slug: str
    title: str
    body: Optional[str] = None
    sections: List[Dict[str, Any]] = Field(default_factory=list)


class PortfolioItem(ContentBase):
    slug: str
    title: str
    body: str
    tags: List[str] = Field(default_factory=list)
    featured: bool = False
    thumbnail_url: str = ""
    date: Optional[str] = None
    excerpt: Optional[str] = None


class BrandSettings(BaseModel):
    """Site-wide brand identity — favicon URLs, social links."""
    favicon_light_url: str = ""
    favicon_dark_url: str = ""
    linkedin: Optional[str] = None
    instagram: Optional[str] = None
    email: Optional[str] = None


class HomepageSettings(SEOMixin):
    """Homepage-specific content and SEO settings."""
    tagline: Optional[str] = None
    bio: Optional[str] = None
    hero_image_url: Optional[str] = None
    cta_text: Optional[str] = None
    cta_url: Optional[str] = None

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ThemeMode(str, Enum):
    dark = "dark"
    light = "light"


class ThemeStyle(str, Enum):
    professional = "professional"
    thoughts = "thoughts"


class ContentBase(BaseModel):
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

from enum import Enum
from typing import Any, Dict, List, Optional, Sequence

from starlette.requests import Request
from starlette_admin.fields import (
    BooleanField,
    EnumField,
    StringField,
    TagsField,
    TextAreaField,
)
from starlette_admin.base import BaseModelView

from ..db import delete_content, get_content, list_content, put_content
from ..models import ThemeMode, ThemeStyle

THEME_FIELDS = [
    EnumField("theme_mode", label="Mode", enum=ThemeMode, required=True),
    EnumField("theme_style", label="Style", enum=ThemeStyle, required=True),
]


def _normalize(data: Dict) -> Dict:
    """Convert Enum instances to string values for DynamoDB storage."""
    return {k: v.value if isinstance(v, Enum) else v for k, v in data.items()}


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

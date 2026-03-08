from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from ..constants import CONTENT_POST
from ..db import get_content, list_content
from ..models import Post

router = APIRouter(tags=["posts"])


@router.get("/posts", response_model=List[Post])
def get_posts(
    limit: int = Query(default=10, le=100),
    published: bool = True,
    tag: Optional[str] = None,
) -> List[dict]:
    items = list_content(CONTENT_POST)
    items = [i for i in items if i.get("published") == published]
    if tag:
        items = [i for i in items if tag in i.get("tags", [])]
    items.sort(key=lambda x: x.get("date", ""), reverse=True)
    return items[:limit]


@router.get("/posts/{slug}", response_model=Post)
def get_post(slug: str) -> dict:
    item = get_content(CONTENT_POST, slug)
    if not item or not item.get("published"):
        raise HTTPException(status_code=404, detail="Post not found")
    return item

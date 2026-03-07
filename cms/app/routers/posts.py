from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from ..db import get_content, list_content

router = APIRouter(tags=["posts"])


@router.get("/posts")
def get_posts(
    limit: int = Query(default=10, le=100),
    published: Optional[bool] = None,
    tag: Optional[str] = None,
) -> List[dict]:
    items = list_content("POST")
    if published is not None:
        items = [i for i in items if i.get("published") == published]
    if tag:
        items = [i for i in items if tag in i.get("tags", [])]
    items.sort(key=lambda x: x.get("date", ""), reverse=True)
    return items[:limit]


@router.get("/posts/{slug}")
def get_post(slug: str) -> dict:
    item = get_content("POST", slug)
    if not item:
        raise HTTPException(status_code=404, detail="Post not found")
    return item

from typing import List

from fastapi import APIRouter, HTTPException, Query

from ..constants import CONTENT_PAGE
from ..db import get_content, list_content
from ..models import Page

router = APIRouter(tags=["pages"])


@router.get("/pages", response_model=List[Page])
def get_pages(published: bool = Query(default=True)) -> List[dict]:
    items = list_content(CONTENT_PAGE)
    return [i for i in items if i.get("published") == published]


@router.get("/pages/{slug}", response_model=Page)
def get_page(slug: str) -> dict:
    item = get_content(CONTENT_PAGE, slug)
    if not item or not item.get("published"):
        raise HTTPException(status_code=404, detail="Page not found")
    return item

from typing import List

from fastapi import APIRouter, HTTPException

from ..constants import CONTENT_PAGE
from ..db import get_content, list_content
from ..models import Page

router = APIRouter(tags=["pages"])


@router.get("/pages", response_model=List[Page])
def get_pages() -> List[dict]:
    return list_content(CONTENT_PAGE)


@router.get("/pages/{slug}", response_model=Page)
def get_page(slug: str) -> dict:
    item = get_content(CONTENT_PAGE, slug)
    if not item:
        raise HTTPException(status_code=404, detail="Page not found")
    return item

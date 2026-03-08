from fastapi import APIRouter, HTTPException

from ..constants import CONTENT_CATEGORY
from ..db import get_content, list_content

router = APIRouter(tags=["categories"])


@router.get("/categories")
def list_categories():
    return list_content(CONTENT_CATEGORY)


@router.get("/categories/{slug}")
def get_category(slug: str):
    item = get_content(CONTENT_CATEGORY, slug)
    if not item:
        raise HTTPException(status_code=404, detail="Category not found")
    return item

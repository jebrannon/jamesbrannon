from fastapi import APIRouter, HTTPException

from ..db import get_content

router = APIRouter(tags=["pages"])


@router.get("/pages/{slug}")
def get_page(slug: str) -> dict:
    item = get_content("PAGE", slug)
    if not item:
        raise HTTPException(status_code=404, detail="Page not found")
    return item

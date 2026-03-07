from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from ..db import get_content, list_content

router = APIRouter(tags=["portfolio"])


@router.get("/portfolio")
def get_portfolio(
    featured: Optional[bool] = None,
    limit: int = Query(default=100, le=100),
) -> List[dict]:
    items = list_content("PORTFOLIO")
    if featured is not None:
        items = [i for i in items if i.get("featured") == featured]
    return items[:limit]


@router.get("/portfolio/{slug}")
def get_portfolio_item(slug: str) -> dict:
    item = get_content("PORTFOLIO", slug)
    if not item:
        raise HTTPException(status_code=404, detail="Portfolio item not found")
    return item

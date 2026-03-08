from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from ..constants import CONTENT_PORTFOLIO
from ..db import get_content, list_content
from ..models import PortfolioItem

router = APIRouter(tags=["portfolio"])


@router.get("/portfolio", response_model=List[PortfolioItem])
def get_portfolio(
    featured: Optional[bool] = None,
    limit: int = Query(default=100, le=100),
) -> List[dict]:
    items = list_content(CONTENT_PORTFOLIO)
    if featured is not None:
        items = [i for i in items if i.get("featured") == featured]
    items.sort(key=lambda x: x.get("date", ""), reverse=True)
    return items[:limit]


@router.get("/portfolio/{slug}", response_model=PortfolioItem)
def get_portfolio_item(slug: str) -> dict:
    item = get_content(CONTENT_PORTFOLIO, slug)
    if not item:
        raise HTTPException(status_code=404, detail="Portfolio item not found")
    return item

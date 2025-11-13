from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from ..config import NEWS_DATA_FILE
from .router_utils import read_json_or_404, slice_limit

router = APIRouter()


@router.get("/news/{market_type}", response_model=List[Dict[str, Any]])
def get_news(market_type: str, limit: int = 100):
    if market_type not in ["stock", "polymarket", "bitmex"]:
        raise HTTPException(status_code=404, detail="Market type not found")

    data = read_json_or_404(NEWS_DATA_FILE)
    news_items = slice_limit(data.get(market_type, []), limit, 100, 500)
    return news_items

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from ..config import SOCIAL_DATA_FILE
from .router_utils import read_json_or_404, slice_limit

router = APIRouter()


@router.get("/social/{market_type}", response_model=List[Dict[str, Any]])
def get_social_feed(market_type: str, limit: int = 100):
    if market_type not in ["stock", "polymarket", "bitmex", "forex"]:
        raise HTTPException(status_code=404, detail="Market type not found")

    data = read_json_or_404(SOCIAL_DATA_FILE)
    social_items = slice_limit(data.get(market_type, []), limit, 100, 500)
    return social_items

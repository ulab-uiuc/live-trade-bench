from typing import Any, Dict, List

from fastapi import APIRouter

from ..config import SOCIAL_DATA_FILE
from .router_utils import read_json_or_404, slice_limit

router = APIRouter()


@router.get("/social", response_model=Dict[str, List[Dict[str, Any]]])
def get_social_media(limit: int = 100):
    data = read_json_or_404(SOCIAL_DATA_FILE)
    stock_social = slice_limit(data.get("stock", []), limit, 100, 500)
    polymarket_social = slice_limit(data.get("polymarket", []), limit, 100, 500)
    return {"stock": stock_social, "polymarket": polymarket_social}

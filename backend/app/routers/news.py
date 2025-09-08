from typing import Any, Dict, List

from app.config import NEWS_DATA_FILE
from app.routers.router_utils import read_json_or_404, slice_limit
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("/stock")
async def get_stock_news(limit: int = 100) -> List[Dict[str, Any]]:
    try:
        data = read_json_or_404(NEWS_DATA_FILE)
        items = data.get("stock", [])
        return slice_limit(items, limit, 100, 500)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stock news: {e}")


@router.get("/polymarket")
async def get_polymarket_news(limit: int = 100) -> List[Dict[str, Any]]:
    try:
        data = read_json_or_404(NEWS_DATA_FILE)
        items = data.get("polymarket", [])
        return slice_limit(items, limit, 100, 500)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching polymarket news: {e}"
        )

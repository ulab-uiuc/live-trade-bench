import json
import os
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from app.config import NEWS_DATA_FILE

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("/stock")
async def get_stock_news(limit: int = 25) -> List[Dict[str, Any]]:
    """Get stock market news from JSON file."""
    try:
        if not os.path.exists(NEWS_DATA_FILE):
            raise HTTPException(status_code=404, detail="News data not ready yet.")

        with open(NEWS_DATA_FILE, "r") as f:
            news_data = json.load(f)

        return news_data.get("stock", [])

    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Error reading news data file.")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching stock news: {str(e)}"
        )


@router.get("/polymarket")
async def get_polymarket_news(limit: int = 25) -> List[Dict[str, Any]]:
    """Get polymarket news from JSON file."""
    try:
        if not os.path.exists(NEWS_DATA_FILE):
            raise HTTPException(status_code=404, detail="News data not ready yet.")

        with open(NEWS_DATA_FILE, "r") as f:
            news_data = json.load(f)

        return news_data.get("polymarket", [])

    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Error reading news data file.")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching polymarket news: {str(e)}"
        )

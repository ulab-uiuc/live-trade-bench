from datetime import datetime, timedelta
from typing import Any, Dict, List

from app.data import get_real_news_data
from app.schemas import NewsCategory, NewsImpact
from app.trading_system import get_trading_system
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("/")
async def get_news(
    query: str = Query(default="stock market", description="Search query for news"),
    days: int = Query(
        default=7, ge=1, le=30, description="Number of days to look back"
    ),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    category: NewsCategory | None = Query(default=None),
    impact: NewsImpact | None = Query(default=None),
    hours: int | None = Query(default=None, ge=1, le=168),  # Last X hours (max 1 week)
) -> List[Dict[str, Any]]:
    """Get cached news articles with optional filtering and pagination."""
    try:
        # Get cached news from trading system (now includes stock symbols)
        trading_system = get_trading_system()
        news_data = trading_system.get_cached_news()

        # Convert datetime strings back to datetime objects for filtering
        for item in news_data:
            item["published_at"] = datetime.fromisoformat(item["published_at"])

        # Apply time filter
        if hours:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            news_data = [n for n in news_data if n["published_at"] >= cutoff_time]

        # Apply category filter
        if category:
            news_data = [n for n in news_data if n["category"] == category]

        # Apply impact filter
        if impact:
            news_data = [n for n in news_data if n["impact"] == impact]

        # Sort by publication date (newest first)
        news_data.sort(key=lambda x: x["published_at"], reverse=True)

        # Convert back to ISO strings for JSON response
        for item in news_data:
            item["published_at"] = item["published_at"].isoformat()

        # Apply pagination
        news_data = news_data[offset : offset + limit]

        return news_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching news: {str(e)}")


@router.get("/search/{query}")
async def search_news(
    query: str,
    days: int = Query(
        default=7, ge=1, le=30, description="Number of days to look back"
    ),
    limit: int = Query(default=20, ge=1, le=100),
) -> Dict[str, Any]:
    """Search real news articles by query."""
    try:
        news = get_real_news_data(query=query, days=days)
        return {"query": query, "count": len(news), "news": news[:limit]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching news: {str(e)}")

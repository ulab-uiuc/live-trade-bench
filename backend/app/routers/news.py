from datetime import datetime, timedelta

from app.data import get_real_news_data
from app.schemas import NewsCategory, NewsImpact, NewsItem
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("/", response_model=list[NewsItem])
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
):
    """Get real news articles with optional filtering and pagination."""
    try:
        news = get_real_news_data(query=query, days=days)

        # Apply time filter
        if hours:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            news = [n for n in news if n.published_at >= cutoff_time]

        # Apply category filter
        if category:
            news = [n for n in news if n.category == category]

        # Apply impact filter
        if impact:
            news = [n for n in news if n.impact == impact]

        # Sort by publication date (newest first)
        news.sort(key=lambda x: x.published_at, reverse=True)

        # Apply pagination
        news = news[offset : offset + limit]

        return news
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching news: {str(e)}")


@router.get("/search/{query}")
async def search_news(
    query: str,
    days: int = Query(
        default=7, ge=1, le=30, description="Number of days to look back"
    ),
    limit: int = Query(default=20, ge=1, le=100),
):
    """Search real news articles by query."""
    try:
        news = get_real_news_data(query=query, days=days)
        return {"query": query, "count": len(news), "news": news[:limit]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching news: {str(e)}")

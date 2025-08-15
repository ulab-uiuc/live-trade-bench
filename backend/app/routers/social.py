from app.trading_system import get_trading_system
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/social", tags=["social"])


@router.get("/")
async def get_social_posts(
    category: str = Query(
        default="all",
        description="Reddit category to fetch from ('all' for all categories)",
    ),
    query: str = Query(
        default=None, description="Optional stock ticker or search query"
    ),
    days: int = Query(
        default=7, ge=1, le=30, description="Number of days to look back"
    ),
):
    """Get cached social media data from Reddit."""
    try:
        # Get cached social data from trading system instead of fetching on-demand
        trading_system = get_trading_system()
        social_data = trading_system.get_cached_social()

        # Apply category filter if specified and not 'all'
        if category != "all":
            social_data = [
                post
                for post in social_data
                if post.get("subreddit", "").lower() == category.lower()
            ]

        # Apply query filter if specified
        if query:
            query_lower = query.lower()
            social_data = [
                post
                for post in social_data
                if query_lower in post.get("title", "").lower()
                or query_lower in post.get("content", "").lower()
            ]

        return social_data
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching cached social data: {str(e)}"
        )

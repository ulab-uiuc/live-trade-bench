from fastapi import APIRouter, HTTPException, Query

from app.data import get_real_social_data

router = APIRouter(prefix="/api/social", tags=["social"])


@router.get("/")
async def get_social_posts():
    """Get sample social media posts (placeholder)."""
    # Return empty for now - real data comes from /real endpoint
    return []


@router.get("/real")
async def get_real_social_posts(
    category: str = Query(default="all", description="Reddit category to fetch from ('all' for all categories)"),
    query: str = Query(default=None, description="Optional stock ticker or search query"),
    days: int = Query(default=7, ge=1, le=30, description="Number of days to look back")
):
    """Get real social media data from Reddit. Fetches 5 posts from each category by default."""
    try:
        posts = get_real_social_data(category=category, query=query, days=days)
        return posts
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching real social data: {str(e)}"
        )
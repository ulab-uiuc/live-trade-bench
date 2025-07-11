from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Query

from app.data import get_news_data, get_real_news_data
from app.schemas import NewsCategory, NewsImpact, NewsItem

router = APIRouter(prefix='/api/news', tags=['news'])


@router.get('/', response_model=list[NewsItem])
async def get_news(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    category: NewsCategory | None = Query(default=None),
    impact: NewsImpact | None = Query(default=None),
    hours: int | None = Query(default=None, ge=1, le=168),  # Last X hours (max 1 week)
):
    """Get news articles with optional filtering and pagination."""
    try:
        news = get_news_data()

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
        raise HTTPException(status_code=500, detail=f'Error fetching news: {str(e)}')


@router.get('/real', response_model=list[NewsItem])
async def get_real_news(
    query: str = Query(default='stock market', description='Search query for news'),
    days: int = Query(
        default=7, ge=1, le=30, description='Number of days to look back'
    ),
):
    """Get real news data from Google News."""
    try:
        news = get_real_news_data(query=query, days=days)
        return news
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f'Error fetching real news: {str(e)}'
        )


@router.get('/category/{category}')
async def get_news_by_category(
    category: NewsCategory, limit: int = Query(default=20, ge=1, le=100)
):
    """Get news articles by category."""
    try:
        news = get_news_data()
        category_news = [n for n in news if n.category == category]

        # Sort by publication date (newest first)
        category_news.sort(key=lambda x: x.published_at, reverse=True)

        # Apply limit
        category_news = category_news[:limit]

        return {
            'category': category.value,
            'count': len(category_news),
            'news': category_news,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f'Error fetching category news: {str(e)}'
        )


@router.get('/impact/{impact}')
async def get_news_by_impact(
    impact: NewsImpact, limit: int = Query(default=20, ge=1, le=100)
):
    """Get news articles by impact level."""
    try:
        news = get_news_data()
        impact_news = [n for n in news if n.impact == impact]

        # Sort by publication date (newest first)
        impact_news.sort(key=lambda x: x.published_at, reverse=True)

        # Apply limit
        impact_news = impact_news[:limit]

        return {'impact': impact.value, 'count': len(impact_news), 'news': impact_news}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f'Error fetching impact news: {str(e)}'
        )


@router.get('/search/{query}')
async def search_news(query: str, limit: int = Query(default=20, ge=1, le=100)):
    """Search news articles by title or summary."""
    try:
        news = get_news_data()
        query_lower = query.lower()

        # Search in title and summary
        matching_news = [
            n
            for n in news
            if query_lower in n.title.lower() or query_lower in n.summary.lower()
        ]

        # Sort by publication date (newest first)
        matching_news.sort(key=lambda x: x.published_at, reverse=True)

        # Apply limit
        matching_news = matching_news[:limit]

        return {'query': query, 'count': len(matching_news), 'news': matching_news}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error searching news: {str(e)}')


@router.get('/stats/summary')
async def get_news_stats():
    """Get news statistics summary."""
    try:
        news = get_news_data()

        if not news:
            return {
                'total_articles': 0,
                'categories': {},
                'impact_levels': {},
                'sources': {},
                'latest_article': None,
            }

        # Count by category
        categories = {}
        for item in news:
            category = item.category.value
            categories[category] = categories.get(category, 0) + 1

        # Count by impact
        impact_levels = {}
        for item in news:
            impact = item.impact.value
            impact_levels[impact] = impact_levels.get(impact, 0) + 1

        # Count by source
        sources = {}
        for item in news:
            source = item.source
            sources[source] = sources.get(source, 0) + 1

        # Find latest article
        latest_article = max(news, key=lambda x: x.published_at)

        return {
            'total_articles': len(news),
            'categories': categories,
            'impact_levels': impact_levels,
            'sources': sources,
            'latest_article': {
                'id': latest_article.id,
                'title': latest_article.title,
                'published_at': latest_article.published_at,
                'source': latest_article.source,
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f'Error fetching news stats: {str(e)}'
        )


@router.get('/{news_id}', response_model=NewsItem)
async def get_news_item(news_id: str):
    """Get a specific news item by ID."""
    try:
        news = get_news_data()
        news_item = next((n for n in news if n.id == news_id), None)
        if not news_item:
            raise HTTPException(status_code=404, detail='News item not found')
        return news_item
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f'Error fetching news item: {str(e)}'
        )


@router.get('/trending/topics')
async def get_trending_topics():
    """Get trending topics based on high-impact recent news."""
    try:
        news = get_news_data()

        # Get high-impact news from last 24 hours
        recent_cutoff = datetime.now() - timedelta(hours=24)
        high_impact_news = [
            n
            for n in news
            if n.published_at >= recent_cutoff and n.impact == NewsImpact.HIGH
        ]

        # Extract keywords from titles (simplified approach)
        keywords = []
        for item in high_impact_news:
            words = item.title.lower().split()
            # Filter out common words
            common_words = {
                'the',
                'and',
                'or',
                'but',
                'in',
                'on',
                'at',
                'to',
                'for',
                'of',
                'with',
                'by',
                'a',
                'an',
            }
            meaningful_words = [
                w for w in words if w not in common_words and len(w) > 3
            ]
            keywords.extend(meaningful_words)

        # Count keyword frequency
        keyword_counts = {}
        for keyword in keywords:
            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1

        # Sort by frequency and take top 10
        trending_topics = sorted(
            keyword_counts.items(), key=lambda x: x[1], reverse=True
        )[:10]

        return {
            'trending_topics': [
                {'topic': topic, 'mentions': count} for topic, count in trending_topics
            ],
            'high_impact_articles': len(high_impact_news),
            'time_range': 'last_24_hours',
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f'Error fetching trending topics: {str(e)}'
        )

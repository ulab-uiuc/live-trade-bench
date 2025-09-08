"""
Mock Package - Provide fake but realistic implementations for testing

This package contains mock versions of fetchers and agents that generate
fake but realistic data for testing purposes, without external dependencies.
"""

# Export mock agents
from .mock_agent import (  # Convenience functions
    MockBaseAgent,
    MockPolymarketAgent,
    MockStockAgent,
    create_mock_polymarket_agent,
    create_mock_stock_agent,
)

# Export mock fetchers
from .mock_fetcher import (  # Convenience functions
    MockBaseFetcher,
    MockNewsFetcher,
    MockOptionFetcher,
    MockRedditFetcher,
    MockStockFetcher,
    fetch_current_stock_price,
    fetch_news_data,
    fetch_reddit_posts_by_ticker,
    fetch_reddit_sentiment_data,
    fetch_stock_price,
    fetch_stock_price_on_date,
    fetch_top_from_category,
    fetch_trending_stocks,
)

__all__ = [
    # Mock Fetchers
    "MockBaseFetcher",
    "MockNewsFetcher",
    "MockRedditFetcher",
    "MockStockFetcher",
    "MockOptionFetcher",
    # Fetcher convenience functions
    "fetch_news_data",
    "fetch_top_from_category",
    "fetch_reddit_posts_by_ticker",
    "fetch_reddit_sentiment_data",
    "fetch_trending_stocks",
    "fetch_current_stock_price",
    "fetch_stock_price_on_date",
    "fetch_stock_price",
    # Mock Agents
    "MockBaseAgent",
    "MockStockAgent",
    "MockPolymarketAgent",
    # Agent convenience functions
    "create_mock_stock_agent",
    "create_mock_polymarket_agent",
]

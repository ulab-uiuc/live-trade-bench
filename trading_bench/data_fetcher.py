"""
Data fetcher module for trading bench.

This module provides a unified interface for fetching various types of data:
- Stock and option data from Yahoo Finance
- News data from Google News
- Prediction market data from Polymarket

All functions are imported from specialized modules in the data_fetchers package.
"""

# Import all functions from the modular data fetchers
from .data_fetchers.news_fetcher import (
    fetch_news_data,
)
from .data_fetchers.option_fetcher import (
    calculate_implied_volatility,
    calculate_option_greeks,
    fetch_option_chain,
    fetch_option_data,
    fetch_option_expirations,
    fetch_option_historical_data,
    get_atm_options,
    get_option_chain_summary,
)
from .data_fetchers.polymarket_fetcher import (
    fetch_polymarket_market_details,
    fetch_polymarket_market_stats,
    fetch_polymarket_markets,
    fetch_polymarket_orderbook,
    fetch_polymarket_trades,
    fetch_polymarket_trending_markets,
    search_polymarket_markets,
)
from .data_fetchers.reddit_fetcher import (
    fetch_reddit_posts_by_ticker,
    fetch_reddit_sentiment_data,
    fetch_top_from_category,
    get_available_categories,
    get_available_dates,
    get_reddit_statistics,
)
from .data_fetchers.stock_fetcher import (
    fetch_price_data,
)

# Export all functions for backward compatibility
__all__ = [
    # Stock data
    'fetch_price_data',
    # Option data
    'fetch_option_chain',
    'fetch_option_data',
    'fetch_option_expirations',
    'fetch_option_historical_data',
    'calculate_option_greeks',
    'get_atm_options',
    'calculate_implied_volatility',
    'get_option_chain_summary',
    # News data
    'fetch_news_data',
    # Polymarket data
    'fetch_polymarket_markets',
    'fetch_polymarket_market_details',
    'fetch_polymarket_orderbook',
    'fetch_polymarket_trades',
    'fetch_polymarket_market_stats',
    'search_polymarket_markets',
    'fetch_polymarket_trending_markets',
    # Reddit data
    'fetch_top_from_category',
    'fetch_reddit_posts_by_ticker',
    'fetch_reddit_sentiment_data',
    'get_available_categories',
    'get_available_dates',
    'get_reddit_statistics',
]

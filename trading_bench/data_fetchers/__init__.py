"""
Data fetchers module for trading bench.

This module contains specialized data fetchers for different data sources:
- stock_fetcher: Stock price data from Yahoo Finance
- option_fetcher: Option data from Yahoo Finance
- news_fetcher: News data from Google News
- polymarket_fetcher: Prediction market data from Polymarket
- reddit_fetcher: Reddit posts and comments data from local JSONL files
"""

from .news_fetcher import (
    fetch_news_data,
)
from .option_fetcher import (
    calculate_implied_volatility,
    calculate_option_greeks,
    fetch_option_chain,
    fetch_option_data,
    fetch_option_expirations,
    fetch_option_historical_data,
    get_atm_options,
    get_option_chain_summary,
)
from .polymarket_fetcher import (
    fetch_polymarket_market_details,
    fetch_polymarket_market_stats,
    fetch_polymarket_markets,
    fetch_polymarket_orderbook,
    fetch_polymarket_trades,
    fetch_polymarket_trending_markets,
    search_polymarket_markets,
)
from .reddit_fetcher import (
    fetch_reddit_posts_by_ticker,
    fetch_reddit_sentiment_data,
    fetch_top_from_category,
    get_available_categories,
    get_available_dates,
    get_reddit_statistics,
)
from .stock_fetcher import (
    fetch_price_data,
)

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

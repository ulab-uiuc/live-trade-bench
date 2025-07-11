"""
Data fetchers module for trading bench.

This module contains specialized data fetchers for different data sources:
- stock_fetcher: Stock price data from Yahoo Finance
- news_fetcher: News data from Google News
- option_fetcher: Option data from Yahoo Finance
- polymarket_fetcher: Prediction market data from Polymarket
- reddit_fetcher: Reddit posts and comments data
"""

# Import base fetcher
from trading_bench.fetchers.base_fetcher import BaseFetcher

# Import fetcher classes
from trading_bench.fetchers.news_fetcher import NewsFetcher
from trading_bench.fetchers.option_fetcher import OptionFetcher
from trading_bench.fetchers.polymarket_fetcher import PolymarketFetcher
from trading_bench.fetchers.reddit_fetcher import RedditFetcher
from trading_bench.fetchers.stock_fetcher import StockFetcher

# Import backward compatibility functions
from trading_bench.fetchers.news_fetcher import fetch_news_data
from trading_bench.fetchers.option_fetcher import (
    calculate_implied_volatility,
    calculate_option_greeks,
    fetch_option_chain,
    fetch_option_data,
    fetch_option_expirations,
    fetch_option_historical_data,
    get_atm_options,
    get_option_chain_summary,
)
from trading_bench.fetchers.polymarket_fetcher import (
    fetch_polymarket_market_details,
    fetch_polymarket_market_stats,
    fetch_polymarket_markets,
    fetch_polymarket_orderbook,
    fetch_polymarket_trades,
    fetch_polymarket_trending_markets,
    search_polymarket_markets,
)
from trading_bench.fetchers.reddit_fetcher import (
    fetch_reddit_posts_by_ticker,
    fetch_reddit_sentiment_data,
    fetch_top_from_category,
    get_available_categories,
    get_available_dates,
    get_reddit_statistics,
)
from trading_bench.fetchers.stock_fetcher import fetch_stock_data

__all__ = [
    # Base class
    'BaseFetcher',
    
    # Fetcher classes
    'StockFetcher',
    'NewsFetcher',
    'OptionFetcher',
    'PolymarketFetcher',
    'RedditFetcher',
    
    # Backward compatibility functions
    'fetch_stock_data',
    'fetch_news_data',
    'fetch_option_chain',
    'fetch_option_data',
    'fetch_option_expirations',
    'fetch_option_historical_data',
    'calculate_option_greeks',
    'get_atm_options',
    'calculate_implied_volatility',
    'get_option_chain_summary',
    'fetch_polymarket_markets',
    'fetch_polymarket_market_details',
    'fetch_polymarket_orderbook',
    'fetch_polymarket_trades',
    'fetch_polymarket_market_stats',
    'search_polymarket_markets',
    'fetch_polymarket_trending_markets',
    'fetch_top_from_category',
    'fetch_reddit_posts_by_ticker',
    'fetch_reddit_sentiment_data',
    'get_available_categories',
    'get_available_dates',
    'get_reddit_statistics',
]

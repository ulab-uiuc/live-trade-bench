"""
Data fetchers module for trading bench.

This module contains specialized data fetchers for different data sources:
- stock_fetcher: Stock price data from Yahoo Finance
- news_fetcher: News data from Google News
"""

from trading_bench.fetchers.news_fetcher import fetch_news_data
from trading_bench.fetchers.stock_fetcher import fetch_price_data

__all__ = [
    'fetch_price_data',
    'fetch_news_data',
]

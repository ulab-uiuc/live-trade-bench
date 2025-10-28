#!/usr/bin/env python3
"""Data Fetcher Demo - Stock prices and financial news"""

from datetime import datetime, timedelta
from live_trade_bench.fetchers.stock_fetcher import (
    fetch_trending_stocks,
    fetch_stock_price_with_history,
)
from live_trade_bench.fetchers.news_fetcher import fetch_news_data

print("📊 Data Fetcher Demo")
print("=" * 60)

# Fetch trending stocks
print("\n📈 Fetching trending stocks...")
trending = fetch_trending_stocks(limit=10)
print(f"Trending stocks: {trending}")

# Fetch stock price data
print("\n💰 Fetching AAPL stock data...")
stock_data = fetch_stock_price_with_history("AAPL")
print(stock_data)

# Fetch financial news
print("\n📰 Fetching financial news...")
today = datetime.now().strftime("%Y-%m-%d")
start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
news = fetch_news_data(query="stock market", start_date=start_date, end_date=today, max_pages=1)
print(f"Found {len(news)} news articles:")
for article in news[:5]:
    print(f"- {article['title']}")

print("\n✅ Demo completed!")
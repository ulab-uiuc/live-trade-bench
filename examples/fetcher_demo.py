"""
Enhanced fetcher demo with data analysis capabilities.

This file demonstrates the new unified fetcher architecture with 
data processing and analysis features.
"""

from typing import Any, Dict, List

from live_trade_bench.fetchers import (
    BaseFetcher,
    NewsFetcher,
    PolymarketFetcher,
    StockFetcher,
)
from live_trade_bench.fetchers.news_fetcher import fetch_news_data
from live_trade_bench.fetchers.polymarket_fetcher import (
    fetch_market_price_with_history,
    fetch_trending_markets,
)
from live_trade_bench.fetchers.stock_fetcher import (
    fetch_stock_price_with_history,
    fetch_trending_stocks,
)


def example_stock_fetcher() -> None:
    """Example of enhanced StockFetcher with market analysis."""
    print("=== Enhanced Stock Fetcher Example ===")

    # Create a stock fetcher
    stock_fetcher = StockFetcher(min_delay=0.5, max_delay=1.5)

    try:
        # Get trending stocks for today
        trending_stocks = fetch_trending_stocks(limit=3, for_date=None)
        print(f"Trending stocks: {trending_stocks}")
        
        # Test historical trending (for backtest)
        historical_date = "2024-01-15"
        historical_stocks = fetch_trending_stocks(limit=3, for_date=historical_date)
        print(f"Historical stocks for {historical_date}: {historical_stocks}")

        # Fetch stock data with history for multiple stocks
        market_data = {}
        for ticker in trending_stocks[:2]:  # Test first 2 stocks
            print(f"\nFetching data for {ticker}...")
            stock_data = fetch_stock_price_with_history(ticker)
            market_data[ticker] = stock_data
            
            if stock_data.get("current_price"):
                print(f"{ticker} current price: ${stock_data['current_price']:.2f}")
                history = stock_data.get("price_history", [])
                print(f"{ticker} history: {len(history)} days")
            else:
                print(f"Failed to fetch {ticker} data")


    except Exception as e:
        print(f"Error in stock fetcher demo: {e}")


def example_news_fetcher() -> None:
    """Example of enhanced NewsFetcher with news analysis."""
    print("\n=== Enhanced News Fetcher Example ===")

    try:
        from live_trade_bench.fetchers.news_fetcher import fetch_news_data
        from datetime import datetime, timedelta
        
        # Calculate date range (last 7 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        # Fetch news for Apple
        print("Fetching Apple stock news...")
        news_data = fetch_news_data(
            query="Apple stock earnings",
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            max_pages=1,
            ticker="AAPL"
        )
        
        print(f"Fetched {len(news_data)} news articles")
        if news_data:
            print(f"Latest article: {news_data[0].get('title', 'No title')}")
            
            # Show news summaries
            print(f"\n--- Sample News ---")
            for i, item in enumerate(news_data[:3], 1):
                print(f"{i}. {item.get('title', 'No title')}")
                if item.get('snippet'):
                    print(f"   {item['snippet'][:100]}...")
            
    except Exception as e:
        print(f"Error in news fetcher demo: {e}")


def example_polymarket_fetcher() -> None:
    """Example of enhanced PolymarketFetcher with market analysis."""
    print("\n=== Enhanced Polymarket Fetcher Example ===")

    try:
        # Get trending markets for today
        print("Fetching trending Polymarket markets...")
        trending_markets = fetch_trending_markets(limit=2, for_date=None)
        print(f"Found {len(trending_markets)} trending markets")
        
        # Test historical markets (for backtest)
        historical_date = "2024-01-15"
        historical_markets = fetch_trending_markets(limit=2, for_date=historical_date)
        print(f"Historical markets for {historical_date}: {len(historical_markets)} markets")

        if trending_markets:
            # Fetch market data with history
            market_data = {}
            for market in trending_markets:
                market_id = market.get("id")
                if market_id:
                    print(f"\nFetching data for market: {market.get('question', market_id)}")
                    market_price_data = fetch_market_price_with_history(market_id)
                    market_data[market_id] = {
                        **market_price_data,
                        "question": market.get("question", market_id),
                        "url": market.get("url", "")
                    }
                    
                    current_price = market_price_data.get("current_price")
                    if current_price is not None:
                        print(f"Current price: {current_price:.3f}")
                        history = market_price_data.get("price_history", [])
                        print(f"History: {len(history)} days")


    except Exception as e:
        print(f"Error in Polymarket fetcher demo: {e}")


def example_integrated_workflow() -> None:
    """Example of integrated workflow using multiple fetchers."""
    print("\n=== Integrated Fetcher Workflow ===")
    
    try:
        # Step 1: Get market universe
        print("1. Getting stock universe...")
        stocks = fetch_trending_stocks(limit=2, for_date=None)
        print(f"Selected stocks: {stocks}")
        
        # Step 2: Fetch market data
        print("\n2. Fetching market data...")
        stock_market_data = {}
        for ticker in stocks:
            stock_data = fetch_stock_price_with_history(ticker)
            stock_market_data[ticker] = stock_data
            print(f"  {ticker}: ${stock_data.get('current_price', 'N/A')}")
        
        # Step 3: Fetch news data
        print("\n3. Fetching related news...")
        from live_trade_bench.fetchers.news_fetcher import fetch_news_data
        from datetime import datetime, timedelta
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=3)
        
        all_news = []
        for ticker in stocks[:1]:  # Just test one to avoid too many requests
            news = fetch_news_data(
                query=f"{ticker} stock",
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
                max_pages=1,
                ticker=ticker
            )
            all_news.extend(news)
            print(f"  {ticker}: {len(news)} articles")
        
        # Step 4: Test backtest data
        print("\n4. Testing backtest data...")
        backtest_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        historical_stocks = fetch_trending_stocks(limit=2, for_date=backtest_date)
        print(f"   Historical stocks for {backtest_date}: {historical_stocks}")
        
        if all_news:
            print(f"\n5. Sample news processing:")
            for item in all_news[:2]:
                print(f"   - {item.get('title', 'No title')}")
                print(f"     Date: {item.get('date', 'Unknown')}")
            
    except Exception as e:
        print(f"Error in integrated workflow: {e}")


def example_context_manager() -> None:
    """Example of using fetchers as context managers."""
    print("\n=== Context Manager Example ===")

    # Use fetcher as context manager for automatic cleanup
    with StockFetcher() as fetcher:
        try:
            trending = fetcher.get_trending_stocks(limit=3)
            print(f"Fetched {len(trending)} trending stocks using context manager: {trending}")
        except Exception as e:
            print(f"Error: {e}")


def example_custom_fetcher() -> None:
    """Example of creating a custom fetcher."""
    print("\n=== Custom Fetcher Example ===")

    class CustomFetcher(BaseFetcher):
        """Example custom fetcher that fetches mock data."""

        def fetch(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
            """Fetch mock data based on query."""
            self._rate_limit_delay()  # Use base class rate limiting

            # Simulate API call
            mock_data = [
                {"id": i, "title": f"Mock item {i} for {query}", "value": i * 10}
                for i in range(limit)
            ]

            return mock_data

    # Use custom fetcher
    custom_fetcher = CustomFetcher(min_delay=0.1, max_delay=0.3)
    data = custom_fetcher.fetch("test", limit=5)
    print(f"Custom fetcher returned {len(data)} items")
    print(f"Sample: {data[0]}")


def main() -> None:
    """Run all enhanced fetcher examples."""
    print("Enhanced Fetcher Architecture Examples")
    print("=" * 60)

    example_stock_fetcher()
    example_news_fetcher()
    example_polymarket_fetcher()
    example_integrated_workflow()
    example_context_manager()
    example_custom_fetcher()

    print("\n" + "=" * 60)
    print("All enhanced fetcher examples completed!")
    print("\nUnified fetcher interfaces demonstrated:")
    print("- fetch_trending_* with for_date parameter (None=today, date=historical)")
    print("- fetch_*_price_with_history for both asset types") 
    print("- Single interface for both live and backtest data")
    print("- Completely symmetric design across asset types")
    print("- Minimal, consolidated API surface")


if __name__ == "__main__":
    main()

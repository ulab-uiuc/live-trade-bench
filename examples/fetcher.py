"""
Example usage of the new fetcher architecture.

This file demonstrates how to use the BaseFetcher and its derived classes
for fetching different types of data.
"""

from trading_bench.fetchers import (
    BaseFetcher,
    NewsFetcher,
    OptionFetcher,
    PolymarketFetcher,
    RedditFetcher,
    StockFetcher,
)


def example_stock_fetcher():
    """Example of using StockFetcher."""
    print("=== Stock Fetcher Example ===")

    # Create a stock fetcher with custom delays
    stock_fetcher = StockFetcher(min_delay=0.5, max_delay=1.5)

    # Fetch price data
    try:
        price_data = stock_fetcher.fetch(
            ticker="AAPL",
            start_date="2024-01-01",
            end_date="2024-01-31",
            resolution="D",
        )
        print(f"Fetched {len(price_data)} days of AAPL data")
        print(f"Sample data: {list(price_data.items())[:2]}")
    except Exception as e:
        print(f"Error fetching stock data: {e}")


def example_news_fetcher():
    """Example of using NewsFetcher."""
    print("\n=== News Fetcher Example ===")

    # Create a news fetcher with longer delays for web scraping
    news_fetcher = NewsFetcher(min_delay=3.0, max_delay=7.0)

    # Fetch news data
    try:
        news_data = news_fetcher.fetch(
            query="Apple stock",
            start_date="2024-01-01",
            end_date="2024-01-31",
            max_pages=2,
        )
        print(f"Fetched {len(news_data)} news articles")
        if news_data:
            print(f"Sample article: {news_data[0]['title']}")
    except Exception as e:
        print(f"Error fetching news data: {e}")


def example_option_fetcher():
    """Example of using OptionFetcher."""
    print("\n=== Option Fetcher Example ===")

    # Create an option fetcher
    option_fetcher = OptionFetcher()

    try:
        # Get available expirations
        expirations = option_fetcher.fetch_option_expirations("AAPL")
        print(f"AAPL has {len(expirations)} option expirations")

        if expirations:
            # Get option chain for nearest expiration
            option_chain = option_fetcher.fetch_option_chain("AAPL", expirations[0])
            print(
                f"Option chain has {len(option_chain['calls'])} calls and {len(option_chain['puts'])} puts"
            )

            # Calculate Greeks for a sample option
            greeks = option_fetcher.calculate_option_greeks(
                underlying_price=150.0,
                strike=150.0,
                time_to_expiry=0.25,
                risk_free_rate=0.05,
                volatility=0.3,
                option_type="call",
            )
            print(f"Sample Greeks: {greeks}")
    except Exception as e:
        print(f"Error fetching option data: {e}")


def example_polymarket_fetcher():
    """Example of using PolymarketFetcher."""
    print("\n=== Polymarket Fetcher Example ===")

    # Create a Polymarket fetcher
    poly_fetcher = PolymarketFetcher()

    try:
        # Fetch trending markets using the unified fetch method
        trending = poly_fetcher.fetch("markets", category=None, limit=5)
        print(f"Found {len(trending)} trending markets")

        if trending:
            # Get details for first market
            market_id = trending[0]["id"]
            details = poly_fetcher.fetch("market_details", market_id=market_id)
            print(f"Market: {details['title']}")
            print(f"Outcomes: {len(details['outcomes'])}")

            # Get orderbook
            orderbook = poly_fetcher.fetch("orderbook", market_id=market_id)
            print(
                f"Orderbook has {len(orderbook['bids'])} bids and {len(orderbook['asks'])} asks"
            )
    except Exception as e:
        print(f"Error fetching Polymarket data: {e}")


def example_reddit_fetcher():
    """Example of using RedditFetcher."""
    print("\n=== Reddit Fetcher Example ===")

    # Create a Reddit fetcher
    reddit_fetcher = RedditFetcher()

    try:
        # Get available categories
        categories = reddit_fetcher.get_available_categories()
        print(f"Available categories: {categories}")

        if categories:
            # Get available dates for first category
            dates = reddit_fetcher.get_available_dates(categories[0])
            print(f"Available dates for {categories[0]}: {len(dates)} dates")

            if dates:
                # Fetch posts for first date
                posts = reddit_fetcher.fetch_top_from_category(
                    category=categories[0], date=dates[0], max_limit=10
                )
                print(f"Fetched {len(posts)} posts")

                if posts:
                    print(f"Top post: {posts[0]['title']}")
    except Exception as e:
        print(f"Error fetching Reddit data: {e}")


def example_context_manager():
    """Example of using fetchers as context managers."""
    print("\n=== Context Manager Example ===")

    # Use fetcher as context manager for automatic cleanup
    with StockFetcher() as fetcher:
        try:
            data = fetcher.fetch("AAPL", "2024-01-01", "2024-01-05", "D")
            print(f"Fetched {len(data)} days of data using context manager")
        except Exception as e:
            print(f"Error: {e}")


def example_custom_fetcher():
    """Example of creating a custom fetcher."""
    print("\n=== Custom Fetcher Example ===")

    class CustomFetcher(BaseFetcher):
        """Example custom fetcher that fetches mock data."""

        def fetch(self, query: str, limit: int = 10):
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


def main():
    """Run all examples."""
    print("Fetcher Architecture Examples")
    print("=" * 50)

    example_stock_fetcher()
    example_news_fetcher()
    example_option_fetcher()
    example_polymarket_fetcher()
    example_reddit_fetcher()
    example_context_manager()
    example_custom_fetcher()

    print("\n" + "=" * 50)
    print("All examples completed!")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Example script demonstrating how to use the modular data fetching structure.

This example shows how to import and use functions from different data fetcher modules.
"""

# Or import from the unified interface (backward compatibility)
# Import from specific modules
from trading_bench.data_fetcher import fetch_news_data as fetch_news_unified
from trading_bench.data_fetcher import \
    fetch_polymarket_trending_markets as fetch_trending_unified
from trading_bench.data_fetcher import fetch_price_data as fetch_price_unified
from trading_bench.data_fetcher import \
    fetch_reddit_posts_by_ticker as fetch_reddit_unified
from trading_bench.data_fetchers.news_fetcher import fetch_news_data
from trading_bench.data_fetchers.polymarket_fetcher import \
    fetch_polymarket_trending_markets
from trading_bench.data_fetchers.reddit_fetcher import \
    fetch_reddit_posts_by_ticker
from trading_bench.data_fetchers.stock_fetcher import fetch_price_data


def demonstrate_modular_imports():
    """Demonstrate importing from specific modules."""

    print('Modular Data Fetching Demo')
    print('=' * 60)

    try:
        # 1. Stock data from stock_fetcher module
        print('1. Fetching stock data using stock_fetcher module:')
        price_data = fetch_price_data('AAPL', '2024-01-01', '2024-01-31')
        print(f'   Successfully fetched {len(price_data)} days of price data')
        print()

        # 2. News data from news_fetcher module
        print('2. Fetching news data using news_fetcher module:')
        news_data = fetch_news_data(
            'AAPL stock', '2024-01-01', '2024-01-31', max_pages=2
        )
        print(f'   Found {len(news_data)} news articles')
        print()

        # 3. Polymarket data from polymarket_fetcher module
        print('3. Fetching trending markets using polymarket_fetcher module:')
        trending_markets = fetch_polymarket_trending_markets(limit=3)
        print(f'   Found {len(trending_markets)} trending markets')
        for i, market in enumerate(trending_markets, 1):
            print(f"   {i}. {market['title']} ({market['category']})")
        print()

        # 4. Reddit data from reddit_fetcher module
        print('4. Fetching Reddit posts using reddit_fetcher module:')
        try:
            reddit_posts = fetch_reddit_posts_by_ticker(
                'AAPL', '2024-01-15', max_limit=3
            )
            print(f'   Found {len(reddit_posts)} posts mentioning AAPL')
            for i, post in enumerate(reddit_posts, 1):
                print(f"   {i}. {post['title'][:50]}...")
        except Exception as e:
            print(f'   Error: {e} (Reddit data path may not exist)')
        print()

    except Exception as e:
        print(f'Error: {e}')


def demonstrate_unified_interface():
    """Demonstrate using the unified interface for backward compatibility."""

    print('\n' + '=' * 60)
    print('Unified Interface Demo (Backward Compatibility)')
    print('=' * 60)

    try:
        # These functions work exactly the same as the modular imports
        print('1. Using unified interface for stock data:')
        price_data = fetch_price_unified('AAPL', '2024-01-01', '2024-01-31')
        print(f'   Successfully fetched {len(price_data)} days of price data')
        print()

        print('2. Using unified interface for news data:')
        news_data = fetch_news_unified(
            'AAPL stock', '2024-01-01', '2024-01-31', max_pages=2
        )
        print(f'   Found {len(news_data)} news articles')
        print()

        print('3. Using unified interface for Polymarket data:')
        trending_markets = fetch_trending_unified(limit=3)
        print(f'   Found {len(trending_markets)} trending markets')
        for i, market in enumerate(trending_markets, 1):
            print(f"   {i}. {market['title']} ({market['category']})")
        print()

        print('4. Using unified interface for Reddit data:')
        try:
            reddit_posts = fetch_reddit_unified('AAPL', '2024-01-15', max_limit=3)
            print(f'   Found {len(reddit_posts)} posts mentioning AAPL')
            for i, post in enumerate(reddit_posts, 1):
                print(f"   {i}. {post['title'][:50]}...")
        except Exception as e:
            print(f'   Error: {e} (Reddit data path may not exist)')
        print()

    except Exception as e:
        print(f'Error: {e}')


def demonstrate_module_specific_features():
    """Demonstrate features specific to each module."""

    print('\n' + '=' * 60)
    print('Module-Specific Features Demo')
    print('=' * 60)

    try:
        # Option fetcher specific features
<<<<<<< HEAD
        from trading_bench.data_fetchers.option_fetcher import \
            calculate_option_greeks
||||||| 66ce20f
        from trading_bench.data_fetchers.option_fetcher import calculate_option_greeks
=======
        from trading_bench.fetchers.option_fetcher import calculate_option_greeks
>>>>>>> 269262685d97fa18f1aef212da6389109d310351

        print('1. Option Fetcher - Greeks Calculation:')
        greeks = calculate_option_greeks(
            underlying_price=100.0,
            strike=100.0,
            time_to_expiry=0.25,
            risk_free_rate=0.05,
            volatility=0.3,
            option_type='call',
        )
        print(f"   Delta: {greeks['delta']:.4f}")
        print(f"   Gamma: {greeks['gamma']:.4f}")
        print(f"   Theta: {greeks['theta']:.4f}")
        print()

        # News fetcher specific features

        print('2. News Fetcher - Custom Request Function:')
        print('   (This function is used internally for rate limiting)')
        print()

        # Polymarket fetcher specific features
<<<<<<< HEAD
        from trading_bench.data_fetchers.polymarket_fetcher import \
            search_polymarket_markets
||||||| 66ce20f
        from trading_bench.data_fetchers.polymarket_fetcher import (
            search_polymarket_markets,
        )
=======
        from trading_bench.fetchers.polymarket_fetcher import (
            search_polymarket_markets,
        )
>>>>>>> 269262685d97fa18f1aef212da6389109d310351

        print('3. Polymarket Fetcher - Market Search:')
        election_markets = search_polymarket_markets('election', category='politics')
        print(f'   Found {len(election_markets)} election-related markets')
        print()

        # Reddit fetcher specific features
<<<<<<< HEAD
        from trading_bench.data_fetchers.reddit_fetcher import \
            get_available_categories
||||||| 66ce20f
        from trading_bench.data_fetchers.reddit_fetcher import get_available_categories
=======
        from trading_bench.fetchers.reddit_fetcher import get_available_categories
>>>>>>> 269262685d97fa18f1aef212da6389109d310351

        print('4. Reddit Fetcher - Category Discovery:')
        try:
            categories = get_available_categories('reddit_data')
            print(f'   Found {len(categories)} available categories')
            for i, category in enumerate(categories[:3], 1):
                print(f'   {i}. {category}')
        except Exception as e:
            print(f'   Error: {e} (Reddit data path may not exist)')
        print()

    except Exception as e:
        print(f'Error: {e}')


if __name__ == '__main__':
    demonstrate_modular_imports()
    demonstrate_unified_interface()
    demonstrate_module_specific_features()

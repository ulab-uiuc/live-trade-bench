#!/usr/bin/env python3
"""
Example script demonstrating how to use the Polymarket data fetching functionality.
"""

from trading_bench.data_fetchers.polymarket_fetcher import (
    fetch_polymarket_market_details,
    fetch_polymarket_market_stats,
    fetch_polymarket_markets,
    fetch_polymarket_orderbook,
    fetch_polymarket_trades,
    fetch_polymarket_trending_markets,
    search_polymarket_markets,
)


def main():
    """Demonstrate Polymarket data fetching functionality."""

    print('Polymarket Data Fetching Demo')
    print('=' * 60)

    try:
        # 1. Get trending markets
        print('1. Trending Markets (Top 5):')
        trending_markets = fetch_polymarket_trending_markets(limit=5)

        for i, market in enumerate(trending_markets, 1):
            print(f"   {i}. {market['title']}")
            print(f"      Category: {market['category']}")
            print(f"      Volume: {market['total_volume']}")
            print(f"      Status: {market['status']}")
            print()

        # 2. Search for specific markets
        print("2. Searching for 'election' markets:")
        election_markets = search_polymarket_markets('election', category='politics')

        for i, market in enumerate(election_markets[:3], 1):
            print(f"   {i}. {market['title']}")
            print(f"      ID: {market['id']}")
            print(f"      Description: {market['description'][:100]}...")
            print()

        # 3. Get market details for a specific market
        if trending_markets:
            sample_market_id = trending_markets[0]['id']
            print(f"3. Market Details for: {trending_markets[0]['title']}")

            market_details = fetch_polymarket_market_details(sample_market_id)

            print(f"   Market ID: {market_details['id']}")
            print(f"   Category: {market_details['category']}")
            print(f"   Status: {market_details['status']}")
            print(f"   Total Volume: {market_details['total_volume']}")
            print(f"   Total Liquidity: {market_details['total_liquidity']}")
            print(f"   Outcomes: {len(market_details['outcomes'])}")
            print()

            # Show outcomes
            print('   Outcomes:')
            for outcome in market_details['outcomes']:
                print(
                    f"     - {outcome['name']}: ${outcome['current_price']:.3f} "
                    f"(Probability: {outcome['probability']:.1f}%)"
                )
            print()

        # 4. Get market statistics
        if trending_markets:
            print('4. Market Statistics:')
            market_stats = fetch_polymarket_market_stats(sample_market_id)

            print(f"   24h Volume: {market_stats['total_volume_24h']}")
            print(f"   Average Price: ${market_stats['average_price']:.3f}")
            print(
                f"   Price Change: {market_stats['price_change']:.3f} "
                f"({market_stats['price_change_percent']:.2f}%)"
            )
            print(f"   Total Trades (24h): {market_stats['total_trades_24h']}")
            print()

        # 5. Get recent trades
        if trending_markets:
            print('5. Recent Trades (Last 5):')
            recent_trades = fetch_polymarket_trades(sample_market_id, limit=5)

            for i, trade in enumerate(recent_trades, 1):
                print(
                    f"   {i}. {trade['side'].upper()} {trade['size']} @ ${trade['price']:.3f}"
                )
            print()

        # 6. Get order book
        if trending_markets and market_details['outcomes']:
            print('6. Order Book (First Outcome):')
            first_outcome_id = market_details['outcomes'][0]['id']
            orderbook = fetch_polymarket_orderbook(sample_market_id, first_outcome_id)

            print(f"   Market ID: {orderbook['market_id']}")
            print(f"   Outcome ID: {orderbook['outcome_id']}")
            print(f"   Bids: {len(orderbook['bids'])} orders")
            print(f"   Asks: {len(orderbook['asks'])} orders")
            print()

    except Exception as e:
        print(f'Error: {e}')


def demonstrate_category_filtering():
    """Demonstrate filtering markets by category."""

    print('\n' + '=' * 60)
    print('Category Filtering Demo')
    print('=' * 60)

    categories = ['politics', 'sports', 'crypto', 'entertainment']

    for category in categories:
        try:
            print(f"\nMarkets in '{category}' category:")
            markets = fetch_polymarket_markets(category=category, limit=3)

            for i, market in enumerate(markets, 1):
                print(f"  {i}. {market['title']}")
                print(f"     Volume: {market['total_volume']}")
                print(f"     Status: {market['status']}")

        except Exception as e:
            print(f'  Error fetching {category} markets: {e}')


def demonstrate_market_search():
    """Demonstrate market search functionality."""

    print('\n' + '=' * 60)
    print('Market Search Demo')
    print('=' * 60)

    search_queries = ['bitcoin', 'president', 'world cup']

    for query in search_queries:
        try:
            print(f"\nSearching for '{query}':")
            results = search_polymarket_markets(query, limit=3)

            for i, market in enumerate(results, 1):
                print(f"  {i}. {market['title']}")
                print(f"     Category: {market['category']}")
                print(f"     Volume: {market['total_volume']}")

        except Exception as e:
            print(f"  Error searching for '{query}': {e}")


if __name__ == '__main__':
    main()
    demonstrate_category_filtering()
    demonstrate_market_search()

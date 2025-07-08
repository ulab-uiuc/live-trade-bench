#!/usr/bin/env python3
"""
Example script demonstrating how to use the news data fetching functionality.
"""

from trading_bench.data_fetchers.news_fetcher import fetch_news_data


def main():
    """Demonstrate news data fetching functionality."""

    # Example: Fetch news about Apple stock for the last month
    query = 'AAPL stock news'
    start_date = '2024-01-01'
    end_date = '2024-01-31'

    print(f"Fetching news data for query: '{query}'")
    print(f'Date range: {start_date} to {end_date}')
    print('-' * 50)

    try:
        news_results = fetch_news_data(query, start_date, end_date)

        print(f'Found {len(news_results)} news articles:')
        print()

        for i, article in enumerate(news_results, 1):
            print(f'Article {i}:')
            print(f"  Title: {article['title']}")
            print(f"  Source: {article['source']}")
            print(f"  Date: {article['date']}")
            print(f"  Snippet: {article['snippet'][:100]}...")
            print(f"  Link: {article['link']}")
            print()

    except Exception as e:
        print(f'Error fetching news data: {e}')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Example script demonstrating how to use the Reddit data fetching functionality.
This script now uses the live Reddit API via PRAW instead of local JSONL files.
"""

import os
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from trading_bench.fetchers.reddit_fetcher import (
    fetch_reddit_posts_by_ticker,
    fetch_reddit_sentiment_data,
    fetch_top_from_category,
    get_available_categories,
    get_available_dates,
    get_reddit_statistics,
)


def check_reddit_credentials():
    """Check if Reddit API credentials are properly configured."""
    required_vars = ["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_USER_AGENT"]
    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        print("❌ Missing Reddit API credentials:")
        for var in missing:
            print(f"   - {var}")
        print("\nPlease set these environment variables:")
        print("export REDDIT_CLIENT_ID='your_client_id'")
        print("export REDDIT_CLIENT_SECRET='your_client_secret'")
        print("export REDDIT_USER_AGENT='YourApp/1.0'")
        print("\nGet credentials at: https://www.reddit.com/prefs/apps/")
        return False

    print("✅ Reddit API credentials found")
    return True


def main():
    """Demonstrate Reddit data fetching functionality."""

    print("Reddit Live API Data Fetching Demo")
    print("=" * 60)

    # Check credentials first
    if not check_reddit_credentials():
        return

    try:
        # 1. Get available categories
        print("\n1. Available categories:")
        categories = get_available_categories()
        if categories:
            for i, category in enumerate(categories, 1):
                print(f"   {i}. {category}")
        else:
            print("   No categories found.")
            return
        print()

        # 2. Get available dates for a category (returns today's date for live API)
        if categories:
            sample_category = categories[0]
            print(f"2. Available dates for '{sample_category}' (live API):")
            dates = get_available_dates(sample_category)
            if dates:
                print(f"   Live data available for: {dates[0]}")
            else:
                print("   No dates available")
            print()

        # 3. Fetch posts from a category
        if categories and dates:
            sample_date = dates[0]
            print(f"3. Fetching live posts from '{sample_category}':")

            posts = fetch_top_from_category(
                category=sample_category, date=sample_date, max_limit=10
            )

            print(f"   Found {len(posts)} posts")
            for i, post in enumerate(posts[:3], 1):  # Show first 3 posts
                print(f"   {i}. {post['title'][:70]}...")
                print(
                    f"      Upvotes: {post['upvotes']}, Subreddit: r/{post['subreddit']}"
                )
                print(f"      Comments: {post['num_comments']}, Score: {post['score']}")
            if len(posts) > 3:
                print(f"   ... and {len(posts) - 3} more posts")
            print()

        # 4. Fetch posts by ticker symbol
        print("4. Fetching posts mentioning AAPL:")
        aapl_posts = fetch_reddit_posts_by_ticker(
            ticker="AAPL",
            date=sample_date if "sample_date" in locals() else "2024-01-15",
            max_limit=5,
        )

        print(f"   Found {len(aapl_posts)} posts mentioning AAPL")
        for i, post in enumerate(aapl_posts[:2], 1):
            print(f"   {i}. {post['title'][:70]}...")
            print(f"      Upvotes: {post['upvotes']}, Comments: {post['num_comments']}")
            print(f"      Subreddit: r/{post['subreddit']}, Author: {post['author']}")
        print()

        # 5. Get statistics for a category
        if categories and dates:
            print(f"5. Statistics for '{sample_category}':")
            stats = get_reddit_statistics(category=sample_category, date=sample_date)

            print(f"   Total posts analyzed: {stats['total_posts']}")
            print(f"   Total upvotes: {stats['total_upvotes']:,}")
            print(f"   Total comments: {stats['total_comments']:,}")
            print(f"   Average upvotes: {stats['avg_upvotes']:.1f}")
            print(f"   Average comments: {stats['avg_comments']:.1f}")
            print(f"   Subreddits: {', '.join(stats['subreddits'][:5])}")
            if stats["top_post"]:
                print(f"   Top post: {stats['top_post']['title'][:60]}...")
                print(f"   Top post upvotes: {stats['top_post']['upvotes']:,}")
            print()

        # 6. Fetch sentiment data
        if categories and dates:
            print("6. Fetching sentiment data:")
            sentiment_posts = fetch_reddit_sentiment_data(
                category=sample_category, date=sample_date, max_limit=5
            )

            print(f"   Found {len(sentiment_posts)} posts for sentiment analysis")
            for i, post in enumerate(sentiment_posts[:2], 1):
                print(f"   {i}. Engagement score: {post['engagement_score']}")
                print(
                    f"      Text length: {len(post['text_for_sentiment'])} characters"
                )
                print(f"      Title: {post['title'][:50]}...")
            print()

    except ValueError as e:
        if "Reddit API credentials" in str(e):
            print(f"❌ Credential Error: {e}")
        else:
            print(f"❌ Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print("This might be due to Reddit API rate limits or network issues.")


def demonstrate_ticker_search():
    """Demonstrate searching for posts by ticker symbols."""

    if not check_reddit_credentials():
        return

    print("\n" + "=" * 60)
    print("Live Ticker Search Demo")
    print("=" * 60)

    # List of popular tickers to search for
    tickers = ["AAPL", "TSLA", "NVDA", "MSFT", "GOOGL"]
    sample_date = "2024-01-15"  # Date is ignored for live API

    for ticker in tickers:
        try:
            print(f"\nSearching live Reddit for posts mentioning {ticker}:")
            posts = fetch_reddit_posts_by_ticker(
                ticker=ticker, date=sample_date, max_limit=3
            )

            print(f"   Found {len(posts)} recent posts")
            for i, post in enumerate(posts, 1):
                print(f"   {i}. {post['title'][:60]}...")
                print(
                    f"      Upvotes: {post['upvotes']}, Subreddit: r/{post['subreddit']}"
                )
                print(f"      Score: {post['score']}, Author: {post['author']}")

        except Exception as e:
            print(f"   Error searching for {ticker}: {e}")


def demonstrate_category_exploration():
    """Demonstrate exploring different categories."""

    if not check_reddit_credentials():
        return

    print("\n" + "=" * 60)
    print("Live Category Exploration Demo")
    print("=" * 60)

    try:
        categories = get_available_categories()

        for category in categories[:3]:  # Explore first 3 categories
            print(f"\nExploring live data for category: {category}")

            dates = get_available_dates(category)
            if dates:
                sample_date = dates[0]
                print(f"   Live data date: {sample_date}")

                stats = get_reddit_statistics(category, sample_date)
                print(f"   Total posts analyzed: {stats['total_posts']}")
                print(f"   Total upvotes: {stats['total_upvotes']:,}")
                print(f"   Active subreddits: {', '.join(stats['subreddits'][:3])}")

                if stats["top_post"]:
                    print(f"   Top post: {stats['top_post']['title'][:60]}...")
                    print(f"   Top post upvotes: {stats['top_post']['upvotes']:,}")
            else:
                print("   No dates available")

    except Exception as e:
        print(f"Error exploring categories: {e}")


if __name__ == "__main__":
    main()
    demonstrate_ticker_search()
    demonstrate_category_exploration()

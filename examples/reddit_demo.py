#!/usr/bin/env python3
"""
Example script demonstrating how to use the Reddit data fetching functionality.
"""

from trading_bench.data_fetchers.reddit_fetcher import (
    fetch_reddit_posts_by_ticker,
    fetch_reddit_sentiment_data,
    fetch_top_from_category,
    get_available_categories,
    get_available_dates,
    get_reddit_statistics,
)


def main():
    """Demonstrate Reddit data fetching functionality."""

    print("Reddit Data Fetching Demo")
    print("=" * 60)

    try:
        # 1. Get available categories
        print("1. Available categories:")
        categories = get_available_categories()
        if categories:
            for i, category in enumerate(categories, 1):
                print(f"   {i}. {category}")
        else:
            print("   No categories found. Please check your data path.")
            return
        print()

        # 2. Get available dates for a category
        if categories:
            sample_category = categories[0]
            print(f"2. Available dates for '{sample_category}':")
            dates = get_available_dates(sample_category)
            if dates:
                print(f"   Found {len(dates)} dates")
                for i, date in enumerate(dates[:5], 1):  # Show first 5 dates
                    print(f"   {i}. {date}")
                if len(dates) > 5:
                    print(f"   ... and {len(dates) - 5} more dates")
            else:
                print("   No dates found for this category")
            print()

        # 3. Fetch posts from a category
        if categories and dates:
            sample_date = dates[0]
            print(f"3. Fetching posts from '{sample_category}' on {sample_date}:")

            posts = fetch_top_from_category(
                category=sample_category, date=sample_date, max_limit=10
            )

            print(f"   Found {len(posts)} posts")
            for i, post in enumerate(posts[:3], 1):  # Show first 3 posts
                print(f"   {i}. {post['title'][:50]}...")
                print(
                    f"      Upvotes: {post['upvotes']}, Subreddit: {post['subreddit']}"
                )
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
            print(f"   {i}. {post['title'][:50]}...")
            print(f"      Upvotes: {post['upvotes']}, Comments: {post['num_comments']}")
        print()

        # 5. Get statistics for a category
        if categories and dates:
            print(f"5. Statistics for '{sample_category}' on {sample_date}:")
            stats = get_reddit_statistics(category=sample_category, date=sample_date)

            print(f"   Total posts: {stats['total_posts']}")
            print(f"   Total upvotes: {stats['total_upvotes']}")
            print(f"   Total comments: {stats['total_comments']}")
            print(f"   Average upvotes: {stats['avg_upvotes']:.1f}")
            print(f"   Average comments: {stats['avg_comments']:.1f}")
            print(f"   Subreddits: {', '.join(stats['subreddits'][:3])}")
            if stats["top_post"]:
                print(f"   Top post: {stats['top_post']['title'][:50]}...")
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
            print()

    except FileNotFoundError as e:
        print(f"Error: {e}")
        print(
            "Please make sure the reddit_data directory exists and contains the expected structure."
        )
    except Exception as e:
        print(f"Error: {e}")


def demonstrate_ticker_search():
    """Demonstrate searching for posts by ticker symbols."""

    print("\n" + "=" * 60)
    print("Ticker Search Demo")
    print("=" * 60)

    # List of popular tickers to search for
    tickers = ["AAPL", "TSLA", "NVDA", "MSFT", "GOOGL"]
    sample_date = "2024-01-15"

    for ticker in tickers:
        try:
            print(f"\nSearching for posts mentioning {ticker}:")
            posts = fetch_reddit_posts_by_ticker(
                ticker=ticker, date=sample_date, max_limit=3
            )

            print(f"   Found {len(posts)} posts")
            for i, post in enumerate(posts, 1):
                print(f"   {i}. {post['title'][:60]}...")
                print(
                    f"      Upvotes: {post['upvotes']}, Subreddit: {post['subreddit']}"
                )

        except Exception as e:
            print(f"   Error searching for {ticker}: {e}")


def demonstrate_category_exploration():
    """Demonstrate exploring different categories."""

    print("\n" + "=" * 60)
    print("Category Exploration Demo")
    print("=" * 60)

    try:
        categories = get_available_categories()

        for category in categories[:3]:  # Explore first 3 categories
            print(f"\nExploring category: {category}")

            dates = get_available_dates(category)
            if dates:
                sample_date = dates[0]
                print(f"   Sample date: {sample_date}")

                stats = get_reddit_statistics(category, sample_date)
                print(f"   Total posts: {stats['total_posts']}")
                print(f"   Subreddits: {', '.join(stats['subreddits'][:3])}")

                if stats["top_post"]:
                    print(f"   Top post: {stats['top_post']['title'][:50]}...")
            else:
                print("   No dates available")

    except Exception as e:
        print(f"Error exploring categories: {e}")


if __name__ == "__main__":
    main()
    demonstrate_ticker_search()
    demonstrate_category_exploration()

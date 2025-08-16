#!/usr/bin/env python3
"""
Example script demonstrating Reddit data fetching functionality.
Fetches live posts from Reddit API using PRAW.
"""

import sys
from datetime import datetime
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# noqa: E402 - imports after path modification
from live_trade_bench.fetchers.reddit_fetcher import (  # noqa: E402
    fetch_reddit_posts_by_ticker,
    fetch_top_from_category,
    get_available_categories,
    get_reddit_statistics,
)


def main() -> None:
    """Demonstrate Reddit data fetching functionality."""

    print("\n🔴 Reddit Live Data Fetching Demo")
    print("=" * 50)

    try:
        # Get available categories
        categories = get_available_categories()
        print(f"\n✅ Available categories: {', '.join(categories)}")

        # Fetch posts from each category
        print("\n📊 Fetching 5 posts from each category...\n")

        for category in categories:
            print(f"📁 Category: {category.upper()}")
            print("-" * 30)

            try:
                posts = fetch_top_from_category(
                    category=category,
                    date=datetime.now().strftime("%Y-%m-%d"),
                    max_limit=5,
                )

                if posts:
                    for i, post in enumerate(posts, 1):
                        print(f"  {i}. {post['title'][:60]}...")
                        print(
                            f"     👥 r/{post['subreddit']} | "
                            f"👍 {post['upvotes']} | "
                            f"💬 {post['num_comments']}"
                        )
                else:
                    print("  No posts found")

            except Exception as e:
                print(f"  ❌ Error: {e}")

            print()

        # Demonstrate ticker-specific search
        print("🔍 Searching for AAPL mentions...")
        print("-" * 30)

        try:
            aapl_posts = fetch_reddit_posts_by_ticker(
                ticker="AAPL", date=datetime.now().strftime("%Y-%m-%d"), max_limit=3
            )

            if aapl_posts:
                for i, post in enumerate(aapl_posts, 1):
                    print(f"  {i}. {post['title'][:60]}...")
                    print(
                        f"     👥 r/{post['subreddit']} | "
                        f"👍 {post['upvotes']} | "
                        f"💬 {post['num_comments']}"
                    )
            else:
                print("  No AAPL mentions found")

        except Exception as e:
            print(f"  ❌ Error: {e}")

        # Show statistics for company_news category
        print("\n📈 Statistics for 'company_news' category:")
        print("-" * 40)

        try:
            stats = get_reddit_statistics(
                category="company_news", date=datetime.now().strftime("%Y-%m-%d")
            )

            print(f"  Total posts: {stats['total_posts']}")
            print(f"  Total upvotes: {stats['total_upvotes']:,}")
            print(f"  Average upvotes: {stats['avg_upvotes']:.1f}")
            print(f"  Active subreddits: {', '.join(stats['subreddits'][:3])}")

            if stats["top_post"]:
                print(f"  🏆 Top post: {stats['top_post']['title'][:50]}...")
                print(f"      ({stats['top_post']['upvotes']} upvotes)")

        except Exception as e:
            print(f"  ❌ Error: {e}")

        print("\n🎯 Reddit data fetch complete.\n")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure Reddit API credentials are properly configured.")


if __name__ == "__main__":
    main()

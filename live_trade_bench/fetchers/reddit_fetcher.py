"""
Reddit data fetcher for trading bench.

This module provides functions to fetch Reddit posts and comments data
from live Reddit API using PRAW (Python Reddit API Wrapper).
"""

import os
from datetime import datetime
from typing import Optional

import praw

from live_trade_bench.fetchers.base_fetcher import BaseFetcher

# Company name mapping for ticker symbols
TICKER_TO_COMPANY = {
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "GOOGL": "Google",
    "AMZN": "Amazon",
    "TSLA": "Tesla",
    "NVDA": "Nvidia",
    "TSM": "Taiwan Semiconductor Manufacturing Company OR TSMC",
    "JPM": "JPMorgan Chase OR JP Morgan",
    "JNJ": "Johnson & Johnson OR JNJ",
    "V": "Visa",
    "WMT": "Walmart",
    "META": "Meta OR Facebook",
    "AMD": "AMD",
    "INTC": "Intel",
    "QCOM": "Qualcomm",
    "BABA": "Alibaba",
    "ADBE": "Adobe",
    "NFLX": "Netflix",
    "CRM": "Salesforce",
    "PYPL": "PayPal",
    "PLTR": "Palantir",
    "MU": "Micron",
    "SQ": "Block OR Square",
    "ZM": "Zoom",
    "CSCO": "Cisco",
    "SHOP": "Shopify",
    "ORCL": "Oracle",
    "X": "Twitter OR X",
    "SPOT": "Spotify",
    "AVGO": "Broadcom",
    "ASML": "ASML ",
    "TWLO": "Twilio",
    "SNAP": "Snap Inc.",
    "TEAM": "Atlassian",
    "SQSP": "Squarespace",
    "UBER": "Uber",
    "ROKU": "Roku",
    "PINS": "Pinterest",
}

# Subreddit mapping for categories
CATEGORY_SUBREDDITS = {
    "company_news": ["investing", "stocks", "SecurityAnalysis", "ValueInvesting"],
    "options": ["options", "thetagang", "wallstreetbets"],
    "market": ["StockMarket", "investing", "wallstreetbets", "SecurityAnalysis"],
    "tech": ["technology", "stocks", "investing"],
}


class RedditFetcher(BaseFetcher):
    """Fetcher for Reddit data from live Reddit API."""

    def __init__(self, min_delay: float = 1.0, max_delay: float = 3.0):
        """Initialize the Reddit fetcher with API rate limiting delays."""
        super().__init__(min_delay, max_delay)
        self.reddit = self._initialize_reddit_client()

    def _initialize_reddit_client(self) -> praw.Reddit:
        """Initialize Reddit API client with credentials."""
        # Use environment variables if available, otherwise use hardcoded values
        client_id = os.getenv("REDDIT_CLIENT_ID", "FnNW8J67RErQf9jjtCBUtw")
        client_secret = os.getenv(
            "REDDIT_CLIENT_SECRET", "2HgpIGHn7oSkmUMSHDoHgjICJMRyWg"
        )
        user_agent = os.getenv("REDDIT_USER_AGENT", "live trade bench/1.0")

        return praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
        )

    def fetch(
        self,
        category: str,
        query: Optional[str] = None,
        max_limit: int = 50,
        time_filter: str = "day",
    ) -> list[dict]:
        """
        Fetch Reddit posts from live API.

        Args:
            category: Category of subreddits to fetch from
            query: Optional search query (ticker symbol or keyword)
            max_limit: Maximum number of posts to fetch
            time_filter: Reddit time filter ('hour', 'day', 'week', 'month', 'year', 'all')

        Returns:
            List of dictionaries containing post data
        """
        subreddits = CATEGORY_SUBREDDITS.get(category, ["investing"])
        all_posts = []

        for subreddit_name in subreddits:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                posts_per_sub = max(1, max_limit // len(subreddits))

                if query:
                    # Search for specific query in subreddit
                    posts = subreddit.search(
                        query, sort="hot", time_filter=time_filter, limit=posts_per_sub
                    )
                else:
                    # Get hot posts from subreddit
                    posts = subreddit.hot(limit=posts_per_sub)

                post_count = 0
                for post in posts:
                    try:
                        # Filter by query if provided (additional filtering beyond search)
                        if query and not self._post_matches_query(post, query):
                            continue

                        post_data = {
                            "title": post.title,
                            "content": post.selftext,
                            "url": post.url,
                            "upvotes": post.ups,
                            "posted_date": datetime.fromtimestamp(
                                post.created_utc
                            ).strftime("%Y-%m-%d"),
                            "subreddit": post.subreddit.display_name,
                            "score": post.score,
                            "num_comments": post.num_comments,
                            "author": str(post.author) if post.author else "deleted",
                            "created_utc": post.created_utc,
                            "id": post.id,
                        }
                        all_posts.append(post_data)
                        post_count += 1

                        if len(all_posts) >= max_limit:
                            break
                    except Exception as e:
                        print(f"Error processing post from r/{subreddit_name}: {e}")
                        continue

                print(f"Fetched {post_count} posts from r/{subreddit_name}")

                # Apply rate limiting delay
                self._rate_limit_delay()

            except Exception as e:
                print(f"Error fetching from r/{subreddit_name}: {e}")
                continue

            if len(all_posts) >= max_limit:
                break

        return all_posts[:max_limit]

    def _post_matches_query(self, post, query: str) -> bool:
        """Check if post matches the query (ticker symbol)."""
        if not query:
            return True

        # Check title and content for ticker symbol or company name
        text = f"{post.title} {post.selftext}".lower()

        # Check for exact ticker match
        if query.upper() in text.upper():
            return True

        # Check for company name match
        if query.upper() in TICKER_TO_COMPANY:
            company_names = TICKER_TO_COMPANY[query.upper()]
            if "OR" in company_names:
                names = company_names.split(" OR ")
            else:
                names = [company_names]

            for name in names:
                if name.lower() in text:
                    return True

        return False

    def fetch_top_from_category(
        self,
        category: str,
        date: str,
        max_limit: int,
        query: Optional[str] = None,
    ) -> list[dict]:
        """
        Fetches top Reddit posts from a specific category.
        Note: date parameter is ignored for live API (gets recent posts).

        Args:
            category: Category to fetch posts from
            date: Date (ignored for live API)
            max_limit: Maximum number of posts to fetch
            query: Optional ticker symbol to search for

        Returns:
            List of dictionaries containing post data
        """
        return self.fetch(category=category, query=query, max_limit=max_limit)

    def fetch_posts_by_ticker(
        self, ticker: str, date: str, max_limit: int = 50
    ) -> list[dict]:
        """
        Fetches Reddit posts specifically mentioning a given ticker symbol.

        Args:
            ticker: Stock ticker symbol to search for
            date: Date (ignored for live API)
            max_limit: Maximum number of posts to fetch

        Returns:
            List of dictionaries containing post data
        """
        return self.fetch(category="company_news", query=ticker, max_limit=max_limit)

    def fetch_sentiment_data(
        self, category: str, date: str, max_limit: int = 100
    ) -> list[dict]:
        """
        Fetches Reddit posts for sentiment analysis.

        Args:
            category: Category of subreddits to fetch from
            date: Date (ignored for live API)
            max_limit: Maximum number of posts to fetch

        Returns:
            List of dictionaries containing post data with sentiment-relevant fields
        """
        posts = self.fetch(category=category, max_limit=max_limit)

        # Add sentiment analysis fields
        for post in posts:
            post["text_for_sentiment"] = f"{post['title']} {post['content']}"
            post["engagement_score"] = post["upvotes"] + (post["num_comments"] * 2)

        return posts

    def get_available_categories(self) -> list[str]:
        """
        Get list of available categories.

        Returns:
            List of available category names
        """
        return list(CATEGORY_SUBREDDITS.keys())

    def get_available_dates(self, category: str) -> list[str]:
        """
        Get list of available dates for a specific category.
        For live API, returns today's date.

        Args:
            category: Category name

        Returns:
            List containing today's date
        """
        return [datetime.now().strftime("%Y-%m-%d")]

    def get_statistics(self, category: str, date: str) -> dict:
        """
        Get statistics about Reddit posts for a category.

        Args:
            category: Category name
            date: Date (ignored for live API)

        Returns:
            Dictionary containing statistics about the posts
        """
        posts = self.fetch(category=category, max_limit=100)

        if not posts:
            return {
                "total_posts": 0,
                "total_upvotes": 0,
                "total_comments": 0,
                "avg_upvotes": 0,
                "avg_comments": 0,
                "top_post": None,
                "subreddits": [],
            }

        total_upvotes = sum(post["upvotes"] for post in posts)
        total_comments = sum(post["num_comments"] for post in posts)
        subreddits = list(set(post["subreddit"] for post in posts))

        # Find top post
        top_post = max(posts, key=lambda x: x["upvotes"])

        return {
            "total_posts": len(posts),
            "total_upvotes": total_upvotes,
            "total_comments": total_comments,
            "avg_upvotes": total_upvotes / len(posts),
            "avg_comments": total_comments / len(posts),
            "top_post": {
                "title": top_post["title"],
                "upvotes": top_post["upvotes"],
                "subreddit": top_post["subreddit"],
            },
            "subreddits": subreddits,
        }


def fetch_top_from_category(
    category: str,
    date: str,
    max_limit: int,
    query: Optional[str] = None,
) -> list[dict]:
    """Backward compatibility function."""
    fetcher = RedditFetcher()
    return fetcher.fetch_top_from_category(category, date, max_limit, query)


def fetch_reddit_posts_by_ticker(
    ticker: str, date: str, max_limit: int = 50
) -> list[dict]:
    """Backward compatibility function."""
    fetcher = RedditFetcher()
    return fetcher.fetch_posts_by_ticker(ticker, date, max_limit)


def fetch_reddit_sentiment_data(
    category: str, date: str, max_limit: int = 100
) -> list[dict]:
    """Backward compatibility function."""
    fetcher = RedditFetcher()
    return fetcher.fetch_sentiment_data(category, date, max_limit)


def get_available_categories() -> list[str]:
    """Backward compatibility function."""
    fetcher = RedditFetcher()
    return fetcher.get_available_categories()


def get_available_dates(category: str) -> list[str]:
    """Backward compatibility function."""
    fetcher = RedditFetcher()
    return fetcher.get_available_dates(category)


def get_reddit_statistics(category: str, date: str) -> dict:
    """Backward compatibility function."""
    fetcher = RedditFetcher()
    return fetcher.get_statistics(category, date)

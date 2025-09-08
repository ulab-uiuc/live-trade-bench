import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import praw

from live_trade_bench.fetchers.base_fetcher import BaseFetcher

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

CATEGORY_SUBREDDITS = {
    "company_news": ["investing", "stocks", "SecurityAnalysis", "ValueInvesting"],
    "options": ["options", "thetagang", "wallstreetbets"],
    "market": ["StockMarket", "investing", "wallstreetbets", "SecurityAnalysis"],
    "tech": ["technology", "stocks", "investing"],
}


class RedditFetcher(BaseFetcher):
    def __init__(self, min_delay: float = 1.0, max_delay: float = 3.0):
        super().__init__(min_delay, max_delay)
        self.reddit = self._initialize_reddit_client()

    def _initialize_reddit_client(self) -> praw.Reddit:
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
    ) -> List[Dict[str, Any]]:
        subreddits = CATEGORY_SUBREDDITS.get(category, ["investing"])
        all_posts = []
        for subreddit_name in subreddits:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                posts_per_sub = max(1, max_limit // len(subreddits))
                if query:
                    posts = subreddit.search(
                        query, sort="hot", time_filter=time_filter, limit=posts_per_sub
                    )
                else:
                    posts = subreddit.hot(limit=posts_per_sub)
                post_count = 0
                for post in posts:
                    try:
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
                self._rate_limit_delay()
            except Exception as e:
                print(f"Error fetching from r/{subreddit_name}: {e}")
                continue
            if len(all_posts) >= max_limit:
                break
        return all_posts[:max_limit]

    def _post_matches_query(self, post: Any, query: str) -> bool:
        if not query:
            return True
        text = f"{post.title} {post.selftext}".lower()
        if query.upper() in text.upper():
            return True
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
    ) -> List[Dict[str, Any]]:
        return self.fetch(category=category, query=query, max_limit=max_limit)

    def fetch_posts_by_ticker(
        self, ticker: str, date: str, max_limit: int = 50
    ) -> List[Dict[str, Any]]:
        return self.fetch(category="company_news", query=ticker, max_limit=max_limit)

    def fetch_sentiment_data(
        self, category: str, date: str, max_limit: int = 100
    ) -> List[Dict[str, Any]]:
        posts = self.fetch(category=category, max_limit=max_limit)
        for post in posts:
            post["text_for_sentiment"] = f"{post['title']} {post['content']}"
            post["engagement_score"] = post["upvotes"] + (post["num_comments"] * 2)
        return posts

    def get_available_categories(self) -> List[str]:
        return list(CATEGORY_SUBREDDITS.keys())

    def get_available_dates(self, category: str) -> List[str]:
        return [datetime.now().strftime("%Y-%m-%d")]

    def get_statistics(self, category: str, date: str) -> Dict[str, Any]:
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
) -> List[Dict[str, Any]]:
    fetcher = RedditFetcher()
    return fetcher.fetch_top_from_category(category, date, max_limit, query)


def fetch_reddit_posts_by_ticker(
    ticker: str, date: str, max_limit: int = 50
) -> List[Dict[str, Any]]:
    fetcher = RedditFetcher()
    return fetcher.fetch_posts_by_ticker(ticker, date, max_limit)


def fetch_reddit_sentiment_data(
    category: str, date: str, max_limit: int = 100
) -> List[Dict[str, Any]]:
    fetcher = RedditFetcher()
    return fetcher.fetch_sentiment_data(category, date, max_limit)


def get_available_categories() -> List[str]:
    fetcher = RedditFetcher()
    return fetcher.get_available_categories()


def get_available_dates(category: str) -> List[str]:
    fetcher = RedditFetcher()
    return fetcher.get_available_dates(category)


def get_reddit_statistics(category: str, date: str) -> Dict[str, Any]:
    fetcher = RedditFetcher()
    return fetcher.get_statistics(category, date)

import urllib.parse
from datetime import datetime
from typing import Any, Dict, List, Optional

from live_trade_bench.fetchers.base_fetcher import BaseFetcher

try:
    import os

    import praw

    HAS_PRAW = True
except ImportError:
    praw = None
    HAS_PRAW = False

TICKER_TO_COMPANY = {
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "GOOGL": "Google",
    "AMZN": "Amazon",
    "TSLA": "Tesla",
    "NVDA": "Nvidia",
    "META": "Meta",
    "AMD": "AMD",
    "INTC": "Intel",
    "NFLX": "Netflix",
}

CATEGORY_SUBREDDITS = {
    "company_news": ["stocks", "investing", "StockMarket", "wallstreetbets"],
    "market": ["StockMarket", "investing", "stocks"],
    "tech": ["technology", "stocks"],
}


class RedditFetcher(BaseFetcher):
    def __init__(self, min_delay: float = 0.5, max_delay: float = 1.0):
        super().__init__(min_delay, max_delay)
        self.reddit = self._init_praw() if HAS_PRAW else None

    def _init_praw(self):
        if not HAS_PRAW:
            return None

        client_id = os.getenv("REDDIT_CLIENT_ID")
        client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        user_agent = os.getenv("REDDIT_USER_AGENT", "live-trade-bench/1.0")

        if not client_id or not client_secret:
            return None

        try:
            return praw.Reddit(
                client_id=client_id, client_secret=client_secret, user_agent=user_agent
            )
        except Exception:
            return None

    def fetch(
        self,
        category: str,
        query: Optional[str] = None,
        max_limit: int = 50,
        time_filter: str = "week",
    ) -> List[Dict[str, Any]]:
        if self.reddit:
            try:
                return self._fetch_with_praw(category, query, max_limit, time_filter)
            except Exception:
                pass
        return self._fetch_with_json(category, query, max_limit, time_filter)

    def _fetch_with_praw(
        self, category: str, query: Optional[str], max_limit: int, time_filter: str
    ) -> List[Dict[str, Any]]:
        subreddits = CATEGORY_SUBREDDITS.get(category, ["investing"])
        posts = []
        seen_ids = set()

        print(
            f"      - PRAW: Fetching from subreddits: {subreddits} for query '{query}' (limit: {max_limit})"
        )

        for subreddit_name in subreddits:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)

                if query:
                    submissions = subreddit.search(
                        query, sort="top", time_filter=time_filter, limit=max_limit
                    )
                else:
                    submissions = subreddit.top(
                        time_filter=time_filter, limit=max_limit
                    )

                for post in submissions:
                    if post.id in seen_ids or len(posts) >= max_limit:
                        print(
                            f"        - PRAW: Skipping duplicate or max limit reached for {subreddit_name}"
                        )
                        continue

                    seen_ids.add(post.id)
                    posts.append(
                        {
                            "title": post.title,
                            "content": post.selftext,
                            "url": f"https://www.reddit.com{post.permalink}",  # Use permalink
                            "upvotes": post.ups,
                            "score": post.score,
                            "num_comments": post.num_comments,
                            "subreddit": post.subreddit.display_name,
                            "author": str(post.author) if post.author else "deleted",
                            "posted_date": datetime.fromtimestamp(
                                post.created_utc
                            ).strftime("%Y-%m-%d"),
                            "created_utc": post.created_utc,
                            "id": post.id,
                        }
                    )
                    print(
                        f"        - PRAW: Collected {len(posts)} posts from {subreddit_name}"
                    )

                    if len(posts) >= max_limit:
                        print(
                            f"        - PRAW: Max limit {max_limit} reached for PRAW fetch. Breaking."
                        )
                        break

            except Exception as e:
                print(f"        - PRAW: Error fetching from {subreddit_name}: {e}")
                continue

        print(f"      - PRAW: Returning {len(posts)} total posts.")
        return posts

    def _fetch_with_json(
        self, category: str, query: Optional[str], max_limit: int, time_filter: str
    ) -> List[Dict[str, Any]]:
        subreddits = CATEGORY_SUBREDDITS.get(category, ["investing"])
        posts = []
        seen_ids = set()

        print(
            f"      - JSON: Fetching from subreddits: {subreddits} for query '{query}' (limit: {max_limit})"
        )

        for subreddit_name in subreddits:
            try:
                if query:
                    encoded_query = urllib.parse.quote(query)
                    url = f"https://www.reddit.com/r/{subreddit_name}/search.json?q={encoded_query}&restrict_sr=1&sort=top&t={time_filter}&limit={max_limit}&raw_json=1"
                else:
                    url = f"https://www.reddit.com/r/{subreddit_name}/top.json?t={time_filter}&limit={max_limit}&raw_json=1"

                print(f"        - JSON: Requesting URL: {url}")
                response = self.make_request(url, timeout=5)
                data = self.safe_json_parse(response, f"reddit r/{subreddit_name}")

                if not data or "data" not in data:
                    print(
                        f"        - JSON: No data or invalid data for {subreddit_name}"
                    )
                    continue

                children = data["data"].get("children", [])
                print(
                    f"        - JSON: Found {len(children)} raw items for {subreddit_name}"
                )

                for child in children:
                    post_data = child.get("data", {})
                    post_id = post_data.get("id")

                    if post_id in seen_ids or len(posts) >= max_limit:
                        print(
                            f"        - JSON: Skipping duplicate or max limit reached for {subreddit_name}"
                        )
                        continue

                    seen_ids.add(post_id)
                    created_utc = post_data.get("created_utc", 0)

                    posts.append(
                        {
                            "title": post_data.get("title", ""),
                            "content": post_data.get("selftext", ""),
                            "url": f'https://www.reddit.com{post_data.get("permalink", "")}',  # Use permalink
                            "upvotes": post_data.get("ups", 0),
                            "score": post_data.get("score", 0),
                            "num_comments": post_data.get("num_comments", 0),
                            "subreddit": post_data.get("subreddit", ""),
                            "author": post_data.get("author", "deleted"),
                            "posted_date": datetime.fromtimestamp(created_utc).strftime(
                                "%Y-%m-%d"
                            )
                            if created_utc
                            else "",
                            "created_utc": created_utc,
                            "id": post_id,
                        }
                    )
                    print(
                        f"        - JSON: Collected {len(posts)} posts from {subreddit_name}"
                    )

                    if len(posts) >= max_limit:
                        print(
                            f"        - JSON: Max limit {max_limit} reached for JSON fetch. Breaking."
                        )
                        break

            except Exception as e:
                print(f"        - JSON: Error fetching from {subreddit_name}: {e}")
                continue

        print(f"      - JSON: Returning {len(posts)} total posts.")
        return posts

    def fetch_top_from_category(
        self, category: str, date: str, max_limit: int, query: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        return self.fetch(category=category, query=query, max_limit=max_limit)

    def fetch_posts_by_ticker(
        self, ticker: str, date: str, max_limit: int = 50
    ) -> List[Dict[str, Any]]:
        queries = [f"${ticker}"]
        if ticker in TICKER_TO_COMPANY:
            queries.append(TICKER_TO_COMPANY[ticker])

        query = " OR ".join(queries)
        return self.fetch(
            category="company_news", query=query, max_limit=max_limit, time_filter="day"
        )

    def fetch_sentiment_data(
        self, category: str, date: str, max_limit: int = 100
    ) -> List[Dict[str, Any]]:
        posts = self.fetch(category=category, max_limit=max_limit)
        for post in posts:
            post[
                "text_for_sentiment"
            ] = f"{post.get('title', '')} {post.get('content', '')}".strip()
            post["engagement_score"] = (
                post.get("upvotes", 0) + post.get("num_comments", 0) * 2
            )
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

        total_upvotes = sum(p.get("upvotes", 0) for p in posts)
        total_comments = sum(p.get("num_comments", 0) for p in posts)
        subreddits = list({p.get("subreddit", "") for p in posts if p.get("subreddit")})
        top_post = max(posts, key=lambda x: x.get("upvotes", 0))

        return {
            "total_posts": len(posts),
            "total_upvotes": total_upvotes,
            "total_comments": total_comments,
            "avg_upvotes": total_upvotes / len(posts) if posts else 0,
            "avg_comments": total_comments / len(posts) if posts else 0,
            "top_post": {
                "title": top_post.get("title", ""),
                "upvotes": top_post.get("upvotes", 0),
                "subreddit": top_post.get("subreddit", ""),
            },
            "subreddits": subreddits,
        }


def fetch_top_from_category(
    category: str, date: str, max_limit: int, query: Optional[str] = None
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

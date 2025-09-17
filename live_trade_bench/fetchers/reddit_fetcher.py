import urllib.parse
from datetime import datetime
from typing import Any, Dict, List, Optional

from live_trade_bench.fetchers.constants import TICKER_TO_COMPANY, CATEGORY_SUBREDDITS
from live_trade_bench.fetchers.base_fetcher import BaseFetcher

try:
    import os

    import praw

    HAS_PRAW = True
except ImportError:
    praw = None
    HAS_PRAW = False


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
        processed_query = query  # Start with the original query

        if query and category == "market":
            # For polymarket questions, if a ticker is embedded, augment the query
            words = query.split()
            tickers_found_in_polymarket_query = []
            for word in words:
                # Check for direct ticker matches or company names that might be tickers
                if len(word) <= 5 and word.upper() in TICKER_TO_COMPANY:
                    tickers_found_in_polymarket_query.append(word.upper())

            if tickers_found_in_polymarket_query:
                # Get unique company names for expansion
                company_names = list(
                    set(
                        [
                            TICKER_TO_COMPANY[t]
                            for t in tickers_found_in_polymarket_query
                        ]
                    )
                )
                # Combine original polymarket query with company names for broader search
                if company_names:
                    processed_query = f"{query} OR {' OR '.join(company_names)}"
                print(
                    f"      - Fetcher: Polymarket query augmented for tickers: '{processed_query}'"
                )

        # For "company_news" category, the query is expected to be already structured by fetch_posts_by_ticker
        # So, no further processing of 'query' is needed here for 'company_news'.

        if self.reddit:
            try:
                return self._fetch_with_praw(
                    category, processed_query, max_limit, time_filter
                )
            except Exception:
                pass
        return self._fetch_with_json(category, processed_query, max_limit, time_filter)

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



def fetch_reddit_posts_by_ticker(
    ticker: str, date: str, max_limit: int = 50
) -> List[Dict[str, Any]]:
    fetcher = RedditFetcher()
    return fetcher.fetch_posts_by_ticker(ticker, date, max_limit)

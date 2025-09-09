import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
import re

import praw

from live_trade_bench.fetchers.base_fetcher import BaseFetcher

# ---- 常见股票别名（保留你的接口与键值） ----
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
    "ASML": "ASML",  # 修正尾部空格
    "TWLO": "Twilio",
    "SNAP": "Snap Inc.",
    "TEAM": "Atlassian",
    "SQSP": "Squarespace",
    "UBER": "Uber",
    "ROKU": "Roku",
    "PINS": "Pinterest",
}

CATEGORY_SUBREDDITS = {
    "company_news": [
        # 将 "all" 放在最后以降低不稳定性；如需可移除
        "StockMarket",
        "stocks",
        "investing",
        "wallstreetbets",
        "SecurityAnalysis",
        "ValueInvesting",
        "all",
    ],
    "options": ["options", "thetagang", "wallstreetbets"],
    "market": ["StockMarket", "investing", "wallstreetbets", "stocks"],
    "tech": ["technology", "stocks", "investing"],
}


class RedditFetcher(BaseFetcher):
    def __init__(self, min_delay: float = 1.0, max_delay: float = 3.0):
        super().__init__(min_delay, max_delay)
        self.reddit = self._initialize_reddit_client()

    def _initialize_reddit_client(self) -> praw.Reddit:
        client_id = os.getenv("REDDIT_CLIENT_ID")
        client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        user_agent = os.getenv("REDDIT_USER_AGENT") or "live-trade-bench/1.0 (contact: you@example.com)"

        if not client_id or not client_secret:
            raise RuntimeError(
                "Missing Reddit credentials. Please set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET."
            )

        return praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
            check_for_async=False,  # PRAW 建议在同步环境下显式关闭
            # requestor_kwargs={"timeout": 30},  # 如需可开启
        )

    def fetch(
        self,
        category: str,
        query: Optional[Union[str, List[str]]] = None,
        max_limit: int = 50,
        time_filter: str = "day",
    ) -> List[Dict[str, Any]]:
        """按类别和可选查询词抓取帖子；保持原接口。"""
        subreddits = CATEGORY_SUBREDDITS.get(category, ["investing"])
        # 将 r/all 放到最后，稳定性更好；若不在列表中则不动
        subs_has_all = [s.lower() for s in subreddits]
        subs_ordered = [s for s in subreddits if s.lower() != "all"]
        if "all" in subs_has_all:
            subs_ordered.append("all")

        # 统一为查询列表（可为 None 表示不带 query）
        if isinstance(query, list):
            queries: List[Optional[str]] = [q for q in query if q]
        elif isinstance(query, str) and query.strip():
            queries = [query.strip()]
        else:
            queries = [None]

        all_posts: List[Dict[str, Any]] = []
        seen_ids = set()
        per_sub = max(2, max_limit // max(1, len(subreddits)))

        for subreddit_name in subs_ordered:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                collected_count_this_sub = 0

                for q in queries:
                    candidates = []
                    try:
                        if q:
                            # 多策略 + 多时间窗口，尽量补足
                            for srt in ("relevance", "new", "top", "hot"):
                                for tf in (time_filter, "week", "month"):
                                    try:
                                        found = list(
                                            subreddit.search(q, sort=srt, time_filter=tf, limit=per_sub)
                                        )
                                        candidates.extend(found)
                                        if len(candidates) >= per_sub:
                                            break
                                if len(candidates) >= per_sub:
                                    break
                        else:
                            candidates = list(subreddit.top(time_filter=time_filter, limit=per_sub))
                            # 兜底追加周榜
                            try:
                                candidates += list(subreddit.top(time_filter="week", limit=per_sub))
                            except Exception:
                                pass
                    except Exception as e:
                        print(f"Error searching r/{subreddit_name} with q={q}: {e}")
                        continue

                    # 处理 / 过滤 / 去重
                    for post in candidates:
                        try:
                            if post.id in seen_ids:
                                continue
                            if q and not self._post_matches_query(post, q):
                                continue

                            post_data = {
                                "title": getattr(post, "title", "") or "",
                                "content": getattr(post, "selftext", "") or "",
                                "url": getattr(post, "url", "") or "",
                                "upvotes": getattr(post, "ups", 0),
                                "posted_date": datetime.fromtimestamp(post.created_utc).strftime("%Y-%m-%d"),
                                "subreddit": post.subreddit.display_name,
                                "score": getattr(post, "score", 0),
                                "num_comments": getattr(post, "num_comments", 0),
                                "author": str(post.author) if getattr(post, "author", None) else "deleted",
                                "created_utc": post.created_utc,
                                "id": post.id,
                            }

                            all_posts.append(post_data)
                            seen_ids.add(post.id)
                            collected_count_this_sub += 1

                            if len(all_posts) >= max_limit:
                                break
                        except Exception as e:
                            print(f"Error processing post from r/{subreddit_name}: {e}")
                            continue

                    if len(all_posts) >= max_limit:
                        break

                print(f"Fetched {collected_count_this_sub} posts from r/{subreddit_name}")
                self._rate_limit_delay()

            except Exception as e:
                print(f"Error fetching from r/{subreddit_name}: {e}")
                continue

            if len(all_posts) >= max_limit:
                break

        return all_posts[:max_limit]

    def _post_matches_query(self, post: Any, query: str) -> bool:
        """尽量严格但实用的匹配：优先 $TICKER，其次公司别名。"""
        if not query:
            return True
        title = getattr(post, "title", "") or ""
        body = getattr(post, "selftext", "") or ""
        text = f"{title} {body}"
        q = query.strip().upper()

        # $T / $TSLA / TSLA 等
        try:
            if len(q) <= 2:
                pat = re.compile(rf"\${re.escape(q)}\b", re.IGNORECASE)
            else:
                pat = re.compile(rf"(\${re.escape(q)}\b|\b{re.escape(q)}\b)", re.IGNORECASE)
            if pat.search(text):
                return True
        except re.error:
            pass

        # 公司别名
        if q in TICKER_TO_COMPANY:
            names = TICKER_TO_COMPANY[q]
            aliases = names.split(" OR ") if "OR" in names else [names]
            for name in aliases:
                try:
                    if re.search(rf"\b{re.escape(name)}\b", text, re.IGNORECASE):
                        return True
                except re.error:
                    continue
        return False

    # ---- 下面这些方法保持原接口不变 ----
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
        q = ticker.strip().upper()
        queries: List[str] = []

        # 优先 $TICKER；长度>2 再加裸 TICKER（避免误伤短词）
        queries.append(f"${q}")
        if len(q) > 2:
            queries.append(q)

        # 别名
        aliases = []
        if q in TICKER_TO_COMPANY:
            names = TICKER_TO_COMPANY[q]
            aliases = names.split(" OR ") if "OR" in names else [names]
        for name in aliases:
            queries.append(f'"{name}"')

        # 去重保持顺序
        seen_q = set()
        queries = [x for x in queries if not (x in seen_q or seen_q.add(x))]

        return self.fetch(category="company_news", query=queries, max_limit=max_limit, time_filter="day")

    def fetch_sentiment_data(
        self, category: str, date: str, max_limit: int = 100
    ) -> List[Dict[str, Any]]:
        posts = self.fetch(category=category, max_limit=max_limit)
        for post in posts:
            post["text_for_sentiment"] = f"{post.get('title','')} {post.get('content','')}".strip()
            post["engagement_score"] = int(post.get("upvotes", 0)) + int(post.get("num_comments", 0)) * 2
        return posts

    def get_available_categories(self) -> List[str]:
        return list(CATEGORY_SUBREDDITS.keys())

    def get_available_dates(self, category: str) -> List[str]:
        # Reddit 时间范围动态，这里仍返回“今天”占位，保持接口
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
        total_upvotes = sum(int(p.get("upvotes", 0)) for p in posts)
        total_comments = sum(int(p.get("num_comments", 0)) for p in posts)
        subreddits = sorted({p.get("subreddit", "") for p in posts if p.get("subreddit")})
        top_post = max(posts, key=lambda x: int(x.get("upvotes", 0)))
        return {
            "total_posts": len(posts),
            "total_upvotes": total_upvotes,
            "total_comments": total_comments,
            "avg_upvotes": total_upvotes / len(posts),
            "avg_comments": total_comments / len(posts),
            "top_post": {
                "title": top_post.get("title", ""),
                "upvotes": top_post.get("upvotes", 0),
                "subreddit": top_post.get("subreddit", ""),
            },
            "subreddits": subreddits,
        }


# ---- 顶层函数（保持原接口） ----
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

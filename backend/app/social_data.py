import json
from typing import Dict, List

from live_trade_bench.fetchers.reddit_fetcher import RedditFetcher
from live_trade_bench.fetchers.stock_fetcher import fetch_trending_stocks
from live_trade_bench.fetchers.polymarket_fetcher import fetch_trending_markets

from .config import SOCIAL_DATA_FILE


def update_social_data() -> None:
    print("📱 Updating social media data...")

    data: Dict[str, List[Dict]] = {"stock": [], "polymarket": []}

    fetcher = RedditFetcher()

    # Stock: top tickers → few posts each
    tickers = fetch_trending_stocks(limit=6) or []
    for t in tickers[:6]:
        posts = fetcher.fetch_posts_by_ticker(t, date="today", max_limit=3) or []
        for p in posts[:3]:
            content = (p.get("content") or p.get("title") or "")[:300]
            data["stock"].append(
                {
                    "content": content,
                    "author": p.get("author", "Unknown"),
                    "platform": "Reddit",
                    "url": p.get("url", ""),
                    "created_at": p.get("posted_date", ""),
                    "subreddit": p.get("subreddit", ""),
                    "upvotes": p.get("upvotes", 0),
                    "num_comments": p.get("num_comments", 0),
                    "tag": t,
                }
            )

    # Polymarket: top markets → first words of question as query
    markets = fetch_trending_markets(limit=4) or []
    for m in markets[:4]:
        q = (m.get("question") or str(m.get("id") or "")).strip()
        if not q:
            continue
        query = " ".join(q.split()[:5])
        posts = fetcher.fetch(category="market", query=query, max_limit=3) or []
        for p in posts[:3]:
            content = (p.get("content") or p.get("title") or "")[:300]
            data["polymarket"].append(
                {
                    "content": content,
                    "author": p.get("author", "Unknown"),
                    "platform": "Reddit",
                    "url": p.get("url", ""),
                    "created_at": p.get("posted_date", ""),
                    "subreddit": p.get("subreddit", ""),
                    "upvotes": p.get("upvotes", 0),
                    "num_comments": p.get("num_comments", 0),
                    "question": q,
                }
            )

    with open(SOCIAL_DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)
    print(f"✅ Social media data updated and saved to {SOCIAL_DATA_FILE}")


if __name__ == "__main__":
    update_social_data()

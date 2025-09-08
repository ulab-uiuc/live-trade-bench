"""
Social media data provider using live_trade_bench fetchers
"""

import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any, Dict, List

# 条件导入fetchers
from .config import USE_MOCK_FETCHERS

if USE_MOCK_FETCHERS:
    from live_trade_bench.mock.mock_fetcher import MockRedditFetcher as RedditFetcher
else:
    from live_trade_bench.fetchers.reddit_fetcher import RedditFetcher


def _format_content(content: str) -> str:
    """Format content for better display."""
    if not content:
        return "No content available"

    # Clean up whitespace
    content = " ".join(content.split())

    # Remove URLs
    content = re.sub(
        r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
        "[链接]",
        content,
    )

    # Remove markdown links
    content = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", content)

    # Remove bold/italic markdown
    content = re.sub(r"\*\*([^*]+)\*\*", r"\1", content)
    content = re.sub(r"\*([^*]+)\*", r"\1", content)

    # Truncate if too long
    if len(content) > 300:
        content = content[:300] + "..."

    return content


def _classify_sentiment(content: str) -> str:
    """Classify social media sentiment based on keywords."""
    text = content.lower()

    positive_keywords = [
        "bullish",
        "moon",
        "rocket",
        "pump",
        "buy",
        "long",
        "hold",
        "diamond",
        "strong",
        "growth",
        "profit",
        "gain",
        "rise",
        "up",
        "positive",
        "optimistic",
        "success",
        "win",
        "breakthrough",
        "record",
        "high",
        "surge",
        "rally",
        "boom",
        "thrive",
        "love",
        "great",
        "amazing",
    ]

    negative_keywords = [
        "bearish",
        "dump",
        "crash",
        "sell",
        "short",
        "weak",
        "struggle",
        "decline",
        "drop",
        "loss",
        "down",
        "negative",
        "pessimistic",
        "fail",
        "crisis",
        "low",
        "plunge",
        "slump",
        "recession",
        "hate",
        "terrible",
        "awful",
        "bad",
        "worst",
        "disappointed",
    ]

    positive_count = sum(1 for keyword in positive_keywords if keyword in text)
    negative_count = sum(1 for keyword in negative_keywords if keyword in text)

    if positive_count > negative_count:
        return "positive"
    elif negative_count > positive_count:
        return "negative"
    else:
        return "neutral"


def fetch_trending_stocks() -> List[str]:
    """Fetch trending stock tickers."""
    try:
        if USE_MOCK_FETCHERS:
            from live_trade_bench.mock.mock_fetcher import fetch_trending_stocks
        else:
            from live_trade_bench.fetchers.stock_fetcher import fetch_trending_stocks

        stocks = fetch_trending_stocks()
        return stocks[:10]  # Limit to top 10
    except Exception:
        # Fallback to popular stocks
        return [
            "AAPL",
            "MSFT",
            "GOOGL",
            "AMZN",
            "TSLA",
            "NVDA",
            "META",
            "AMD",
            "NFLX",
            "CRM",
        ]


def extract_keywords_from_question(question: str) -> str:
    """Extract the most important key noun from polymarket question for better search."""
    import re

    # Remove common question words and stop words
    stop_words = {
        "will",
        "be",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "from",
        "up",
        "about",
        "into",
        "through",
        "during",
        "before",
        "after",
        "above",
        "below",
        "between",
        "among",
        "the",
        "a",
        "an",
        "and",
        "or",
        "but",
        "if",
        "then",
        "because",
        "as",
        "until",
        "while",
        "of",
        "to",
        "for",
        "with",
        "on",
        "at",
        "by",
        "from",
        "up",
        "about",
        "into",
        "through",
        "during",
        "before",
        "after",
        "above",
        "below",
        "between",
        "among",
        "is",
        "are",
        "was",
        "were",
        "been",
        "being",
        "have",
        "has",
        "had",
        "having",
        "do",
        "does",
        "did",
        "doing",
        "can",
        "could",
        "should",
        "would",
        "may",
        "might",
        "must",
        "shall",
        "will",
        "this",
        "that",
        "these",
        "those",
        "i",
        "you",
        "he",
        "she",
        "it",
        "we",
        "they",
        "me",
        "him",
        "her",
        "us",
        "them",
        "my",
        "your",
        "his",
        "her",
        "its",
        "our",
        "their",
        "mine",
        "yours",
        "hers",
        "ours",
        "theirs",
        "win",
        "reach",
        "cut",
        "replace",
        "happen",
        "occur",
        "increase",
        "decrease",
        "rise",
        "fall",
        "drop",
        "gain",
        "lose",
        "surpass",
        "exceed",
        "beat",
        "defeat",
        "election",
        "price",
        "rates",
        "jobs",
        "market",
        "year",
        "end",
        "start",
        "begin",
        "finish",
        "complete",
        "achieve",
        "accomplish",
    }

    # Clean the question
    question = re.sub(r"[^\w\s]", " ", question.lower())
    words = question.split()

    # Filter out stop words and short words, prioritize longer words
    keywords = [word for word in words if len(word) > 2 and word not in stop_words]

    # Sort by length (longer words are usually more specific) and take the most important one
    if keywords:
        keywords.sort(key=len, reverse=True)
        return keywords[0]  # Return only the most important key noun

    return "polymarket"  # Fallback


def fetch_trending_markets() -> List[str]:
    """Fetch trending polymarket topics and extract keywords."""
    try:
        if USE_MOCK_FETCHERS:
            # Mock polymarket fetcher - 返回空列表或简单mock数据
            def fetch_trending_markets():
                return [{"id": "mock_market_1", "question": "Mock market"}]

        else:
            from live_trade_bench.fetchers.polymarket_fetcher import (
                fetch_trending_markets,
            )

        markets = fetch_trending_markets()
        # Extract keywords from question text
        topics = []
        for market in markets[:5]:
            if isinstance(market, dict) and "question" in market:
                keywords = extract_keywords_from_question(market["question"])
                if keywords:
                    topics.append(keywords)
            elif isinstance(market, str):
                keywords = extract_keywords_from_question(market)
                if keywords:
                    topics.append(keywords)
        return topics
    except Exception as e:
        print(f"Error fetching trending markets: {e}")
        # Fallback topics with keywords
        return [
            "presidential election 2024",
            "bitcoin price",
            "federal reserve rates",
            "artificial intelligence",
            "climate change",
        ]


def fetch_stock_social(ticker: str) -> List[Dict[str, Any]]:
    """Fetch social media posts for a specific stock ticker."""
    try:
        reddit_fetcher = RedditFetcher()
        # Use today's date and proper parameter name
        today = datetime.now().strftime("%Y-%m-%d")
        raw_posts = reddit_fetcher.fetch_posts_by_ticker(
            ticker, date=today, max_limit=5
        )

        formatted_posts = []
        for i, post in enumerate(raw_posts):
            content = _format_content(post.get("content", ""))
            formatted_posts.append(
                {
                    "id": f"real_stock_{ticker}_{i}_{int(time.time())}",
                    "content": content,
                    "author": post.get("author", "Unknown"),
                    "platform": "Reddit",
                    "created_at": post.get("created_at", datetime.now().isoformat()),
                    "sentiment": _classify_sentiment(content),
                    "upvotes": post.get("upvotes", 0),
                    "category": "stock",
                    "market_type": "stock",
                    "stock_symbols": [ticker],
                    "url": post.get("url", "https://reddit.com/r/stocks"),
                }
            )
        return formatted_posts
    except Exception as e:
        print(f"Error fetching stock social for {ticker}: {e}")
        return []


def fetch_polymarket_social(topic: str) -> List[Dict[str, Any]]:
    """Fetch social media posts for a specific polymarket topic."""
    try:
        reddit_fetcher = RedditFetcher()
        # Use 'market' category instead of 'polymarket' since that's what's available
        raw_posts = reddit_fetcher.fetch(category="market", query=topic, max_limit=5)

        formatted_posts = []
        for i, post in enumerate(raw_posts):
            content = _format_content(post.get("content", ""))
            formatted_posts.append(
                {
                    "id": f"real_polymarket_{topic.replace(' ', '_')}_{i}_{int(time.time())}",
                    "content": content,
                    "author": post.get("author", "Unknown"),
                    "platform": "Reddit",
                    "created_at": post.get("created_at", datetime.now().isoformat()),
                    "sentiment": _classify_sentiment(content),
                    "upvotes": post.get("upvotes", 0),
                    "category": "polymarket",
                    "market_type": "polymarket",
                    "topic": topic,
                    "url": post.get("url", "https://reddit.com/r/polymarket"),
                }
            )
        return formatted_posts
    except Exception as e:
        print(f"Error fetching polymarket social for {topic}: {e}")
        return []


def update_social_data():
    """Update social media data and save to JSON file."""
    try:
        # Fetch social data
        social_data = {"stock": [], "polymarket": []}

        # Get trending stocks and markets
        stocks = fetch_trending_stocks()
        topics = fetch_trending_markets()

        # Fetch stock social posts in parallel
        with ThreadPoolExecutor(max_workers=5) as executor:
            stock_futures = {
                executor.submit(fetch_stock_social, ticker): ticker for ticker in stocks
            }

            for future in as_completed(stock_futures):
                ticker = stock_futures[future]
                try:
                    posts = future.result()
                    social_data["stock"].extend(posts)
                except Exception as e:
                    print(f"Error fetching stock social for {ticker}: {e}")
                    import traceback

                    traceback.print_exc()

        # Fetch polymarket social posts in parallel
        print(f"Fetching polymarket social for topics: {topics}")
        with ThreadPoolExecutor(max_workers=3) as executor:
            polymarket_futures = {
                executor.submit(fetch_polymarket_social, topic): topic
                for topic in topics
            }

            for future in as_completed(polymarket_futures):
                topic = polymarket_futures[future]
                try:
                    posts = future.result()
                    print(f"Got {len(posts)} posts for topic '{topic}'")
                    social_data["polymarket"].extend(posts)
                except Exception as e:
                    print(f"Error fetching polymarket social for {topic}: {e}")
                    import traceback

                    traceback.print_exc()

        # Save to JSON file
        with open("social_data.json", "w") as f:
            json.dump(social_data, f, indent=2)

    except Exception:
        import traceback

        traceback.print_exc()

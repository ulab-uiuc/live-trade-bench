from typing import Any, Dict, List, Optional

from app.schemas import (
    ModelCategory,
    ModelStatus,
    NewsCategory,
    NewsImpact,
    NewsItem,
    Trade,
    TradeType,
    TradingModel,
)

# Import trading system for real data
from app.trading_system import get_trading_system


def get_real_models_data() -> list[TradingModel]:
    """Get real LLM model performance data from actual trading agents."""
    try:
        trading_system = get_trading_system()
        models_data = trading_system.get_model_data()

        # Convert to TradingModel schema
        trading_models = []
        for model_data in models_data:
            # Map status
            status = (
                ModelStatus.ACTIVE
                if model_data["status"] == "active"
                else ModelStatus.INACTIVE
            )

            # Map category
            category_str = model_data.get("category", "stock")
            if category_str == "stock":
                category = ModelCategory.STOCK
            elif category_str == "polymarket":
                category = ModelCategory.POLYMARKET
            else:
                category = ModelCategory.STOCK  # Default fallback

            trading_model = TradingModel(
                id=model_data["id"],
                name=model_data["name"],
                category=category,
                performance=model_data["performance"],  # Return percentage
                accuracy=model_data["accuracy"],  # Profitable trades percentage
                trades=model_data["trades"],  # Number of transactions
                profit=model_data["profit"],  # Total profit/loss
                status=status,
                total_value=model_data.get("total_value"),
                cash_balance=model_data.get("cash_balance"),
                active_positions=model_data.get("active_positions"),
                is_activated=model_data.get("is_activated"),
                recent_performance=model_data.get("recent_performance"),
                llm_available=model_data.get("llm_available"),
                market_type=model_data.get("market_type"),
            )
            trading_models.append(trading_model)

        return trading_models

    except Exception as e:
        print(f"Error getting real models data: {e}")
        # Return empty list - no fallback data
        raise Exception(f"Trading system not available: {e}")


def get_real_trades_data(ticker: str = "NVDA", days: int = 7) -> list[Trade]:
    """Get real trading data by fetching stock prices."""
    import os
    import sys
    from datetime import datetime, timedelta

    # Add live_trade_bench to path
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    sys.path.insert(0, project_root)

    try:
        from examples.stock_price_simulator import StockFetcher

        # Calculate date range
        end_date = datetime.now() - timedelta(days=1)  # Yesterday
        start_date = end_date - timedelta(days=days)

        # Fetch real stock data (StockFetcher returns a pandas DataFrame)
        fetcher = StockFetcher()
        price_df = fetcher.fetch_stock_data(
            ticker=ticker,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=(end_date + timedelta(days=1)).strftime("%Y-%m-%d"),
            interval="1d",
        )

        # If a DataFrame was returned, convert to dict keyed by ISO date strings
        try:
            # Defer import to avoid adding pandas to top-level if not installed
            import pandas as pd

            if isinstance(price_df, pd.DataFrame):
                # Ensure the index is dates and convert to dict with date strings
                df = price_df.copy()
                if df.index.dtype != object:
                    df.index = df.index.astype(str)
                price_data: Dict[str, Dict[str, Any]] = df.to_dict(orient="index")
            elif isinstance(price_df, dict):
                price_data = price_df
            else:
                print(
                    "No price data available for the specified ticker and date range."
                )
                return []
        except Exception:
            # Fallback if pandas is not available or conversion fails
            if isinstance(price_df, dict):
                price_data = price_df
            else:
                print(
                    "No price data available for the specified ticker and date range."
                )
                return []

        # Convert price data to trade records
        trades: List[Trade] = []
        dates = sorted(price_data.keys())

        for i, date_str in enumerate(dates):
            if i < len(dates) - 1:  # Need next day for profit calculation
                data = price_data[date_str]
                next_data = price_data[dates[i + 1]]

                # Simple trading logic: buy if price went up next day
                trade_type = (
                    TradeType.BUY
                    if next_data["close"] > data["close"]
                    else TradeType.SELL
                )

                # Calculate profit (simplified)
                if trade_type == TradeType.BUY:
                    profit = (
                        next_data["close"] - data["close"]
                    ) * 100  # Assume 100 shares
                else:
                    profit = (
                        data["close"] - next_data["close"]
                    ) * 100  # Profit from selling

                trade = Trade(
                    id=str(i + 1),
                    timestamp=datetime.fromisoformat(date_str),
                    symbol=ticker.upper(),
                    type=trade_type,
                    amount=100,  # Fixed 100 shares
                    price=data["close"],
                    profit=profit,
                    model="Real Data Model",
                )
                trades.append(trade)

        return trades

    except Exception as e:
        print(f"Error fetching real trades: {e}")
        raise Exception(f"Unable to fetch trading data: {e}")


def get_real_news_data(query: str = "stock market", days: int = 7) -> list[NewsItem]:
    """Get real news data from Google News, using trending stocks as queries when no specific query provided."""
    import os
    import sys
    from datetime import datetime, timedelta

    # Add live_trade_bench to path
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    sys.path.insert(0, project_root)

    try:
        from live_trade_bench import fetch_trending_stocks
        from live_trade_bench.fetchers.news_fetcher import fetch_news_data

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        raw_news = []

        # If using default query, fetch news for trending stocks
        if query == "stock market":
            try:
                # Get trending stocks to use as news queries
                trending_stocks = fetch_trending_stocks(
                    limit=10
                )  # Use top 10 stocks for news
                print(f"📰 Fetching news for trending stocks: {trending_stocks}")

                for ticker in trending_stocks:
                    stock_query = f"{ticker} stock"
                    print(f"📰 Searching news for: {stock_query}")

                    try:
                        stock_news = fetch_news_data(
                            query=stock_query,
                            start_date=start_date.strftime("%Y-%m-%d"),
                            end_date=end_date.strftime("%Y-%m-%d"),
                            max_pages=1,  # Limit pages per stock to avoid too many requests
                        )
                        # Add stock_symbol metadata to each article
                        for article in stock_news:
                            article["stock_symbol"] = ticker
                        raw_news.extend(stock_news)
                    except Exception as e:
                        print(f"⚠️ Error fetching news for {ticker}: {e}")
                        continue

                # Also add general market news
                try:
                    general_news = fetch_news_data(
                        query="stock market finance",
                        start_date=start_date.strftime("%Y-%m-%d"),
                        end_date=end_date.strftime("%Y-%m-%d"),
                        max_pages=1,
                    )
                    # Add stock_symbol as None for general market news
                    for article in general_news:
                        article["stock_symbol"] = None
                    raw_news.extend(general_news)
                except Exception as e:
                    print(f"⚠️ Error fetching general market news: {e}")

            except Exception as e:
                print(f"⚠️ Error fetching trending stocks for news: {e}")
                # Fallback to default query if trending stocks fail
                raw_news = fetch_news_data(
                    query=query,
                    start_date=start_date.strftime("%Y-%m-%d"),
                    end_date=end_date.strftime("%Y-%m-%d"),
                    max_pages=3,
                )
                # Add stock_symbol as None for fallback news
                for article in raw_news:
                    article["stock_symbol"] = None
        else:
            # Use specific query provided by user
            raw_news = fetch_news_data(
                query=query,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
                max_pages=3,
            )
            # Add stock_symbol as None for user-provided queries
            for article in raw_news:
                article["stock_symbol"] = None

        # Convert to NewsItem format
        news_items = []
        for i, article in enumerate(raw_news[:20]):  # Limit to 20 articles
            try:
                # Parse date or use current time
                try:
                    # Try to parse various date formats
                    if "ago" in article.get("date", ""):
                        published_at = datetime.now() - timedelta(hours=1)
                    else:
                        published_at = datetime.now()
                except Exception:
                    published_at = datetime.now()

                # Determine impact based on keywords
                title_lower = article.get("title", "").lower()
                snippet_lower = article.get("snippet", "").lower()

                if any(
                    word in title_lower or word in snippet_lower
                    for word in [
                        "crash",
                        "surge",
                        "breaking",
                        "major",
                        "federal",
                        "rate",
                    ]
                ):
                    impact = NewsImpact.HIGH
                elif any(
                    word in title_lower or word in snippet_lower
                    for word in ["rises", "falls", "earnings", "report"]
                ):
                    impact = NewsImpact.MEDIUM
                else:
                    impact = NewsImpact.LOW

                # Determine category based on keywords and stock tickers
                # Check if any trending stock tickers appear in the title/snippet
                stock_mentioned = False
                if query == "stock market":
                    try:
                        trending_stocks = fetch_trending_stocks(limit=10)
                        stock_tickers = (
                            trending_stocks  # Already a list of ticker strings
                        )
                        stock_names = [
                            ticker.lower() for ticker in trending_stocks
                        ]  # Use tickers as names

                        if any(
                            ticker in title_lower or ticker in snippet_lower
                            for ticker in stock_tickers
                        ) or any(
                            name in title_lower or name in snippet_lower
                            for name in stock_names
                        ):
                            stock_mentioned = True
                    except Exception:
                        pass

                if any(
                    word in title_lower or word in snippet_lower
                    for word in ["fed", "federal", "rate", "inflation", "economy"]
                ):
                    category = NewsCategory.ECONOMIC
                elif (
                    any(
                        word in title_lower or word in snippet_lower
                        for word in [
                            "tech",
                            "ai",
                            "software",
                            "apple",
                            "google",
                            "microsoft",
                            "nvidia",
                            "tesla",
                            "meta",
                        ]
                    )
                    or stock_mentioned
                ):
                    category = NewsCategory.TECH
                elif (
                    any(
                        word in title_lower or word in snippet_lower
                        for word in ["earnings", "company", "ceo", "revenue", "stock"]
                    )
                    or stock_mentioned
                ):
                    category = NewsCategory.COMPANY
                else:
                    category = NewsCategory.MARKET

                news_item = NewsItem(
                    id=str(i + 1),
                    title=article.get("title", "No title"),
                    summary=article.get("snippet", "No summary"),
                    source=article.get("source", "Unknown"),
                    published_at=published_at,
                    impact=impact,
                    category=category,
                    url=article.get("link", "#"),
                    stock_symbol=article.get("stock_symbol"),
                )
                news_items.append(news_item)

            except Exception as e:
                print(f"Error processing article {i}: {e}")
                continue

        return news_items

    except Exception as e:
        print(f"Error fetching real news: {e}")
        raise Exception(f"Unable to fetch news data: {e}")


def get_real_social_data(
    category: str = "all", query: Optional[str] = None, days: int = 7
) -> List[Dict[str, Any]]:
    """Get real social media data from Reddit across all categories."""
    import os
    import sys
    import warnings
    from datetime import datetime

    # Suppress PRAW async warnings since we're using it correctly in FastAPI
    warnings.filterwarnings("ignore", message=".*PRAW.*asynchronous.*")

    # Also suppress PRAW logging warnings
    import logging

    logging.getLogger("praw").setLevel(logging.ERROR)

    # Add live_trade_bench to path
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    sys.path.insert(0, project_root)

    try:
        from live_trade_bench.fetchers.reddit_fetcher import (
            fetch_top_from_category,
            get_available_categories,
        )

        # Get all available categories
        all_categories = get_available_categories()
        categories_to_fetch = [category] if category != "all" else all_categories

        social_posts = []

        # Fetch 5 posts from each category
        for cat in categories_to_fetch:
            try:
                posts = fetch_top_from_category(
                    category=cat,
                    date=datetime.now().strftime("%Y-%m-%d"),
                    max_limit=5,
                    query=query,
                )
                # Add category info to each post
                for post in posts:
                    post["reddit_category"] = cat
                social_posts.extend(posts)
            except Exception as e:
                print(f"Error fetching Reddit data for category {cat}: {e}")
                continue

        # Convert to social media format
        social_items = []
        for i, post in enumerate(social_posts):
            try:
                # Determine sentiment based on keywords (simplified)
                text = f"{post.get('title', '')} {post.get('content', '')}"
                text_lower = text.lower()

                if any(
                    word in text_lower
                    for word in [
                        "good",
                        "great",
                        "excellent",
                        "bullish",
                        "moon",
                        "rocket",
                        "🚀",
                    ]
                ):
                    sentiment = "positive"
                elif any(
                    word in text_lower
                    for word in ["bad", "terrible", "crash", "bearish", "dump", "sell"]
                ):
                    sentiment = "negative"
                else:
                    sentiment = "neutral"

                # Map Reddit category to frontend category
                reddit_category = post.get("reddit_category", "market")

                # Set the category based on which Reddit category this came from
                if reddit_category == "company_news":
                    post_category = "stock"
                elif reddit_category == "tech":
                    post_category = "tech"
                else:
                    post_category = "market"

                social_item = {
                    "id": str(i + 1),
                    "platform": "reddit",
                    "author": post.get("author", "Unknown"),
                    "content": post.get("content", post.get("title", "No content")),
                    "title": post.get("title", ""),
                    "posted_at": datetime.utcfromtimestamp(
                        post.get("created_utc", 0)
                    ).isoformat(),
                    "upvotes": post.get("upvotes", 0),
                    "comments": post.get("num_comments", 0),
                    "sentiment": sentiment,
                    "category": post_category,
                    "ticker": query if query else None,
                    "url": post.get("url", ""),
                    "subreddit": post.get("subreddit", ""),
                }
                social_items.append(social_item)

            except Exception as e:
                print(f"Error processing social post {i}: {e}")
                continue

        return social_items

    except Exception as e:
        print(f"Error fetching real social data: {e}")
        raise Exception(f"Unable to fetch social media data: {e}")


def get_real_polymarket_data(limit: int = 10) -> List[Dict[str, Any]]:
    """Get real polymarket data from Polymarket API."""
    import os
    import sys
    from datetime import datetime

    # Add live_trade_bench to path
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    sys.path.insert(0, project_root)

    try:
        from live_trade_bench.fetchers.polymarket_fetcher import PolymarketFetcher

        fetcher = PolymarketFetcher()
        markets = fetcher.get_trending_markets(limit=limit)

        if not markets:
            # Return empty list if no real data
            return []

        # Enhanced market data for frontend compatibility
        enhanced_markets: list[dict[str, Any]] = []
        for market in markets:
            if not market.get("id"):
                continue

            # Ensure required fields exist
            market.setdefault("status", "active")
            market.setdefault("title", f"Market {market['id']}")
            market.setdefault("category", "unknown")
            market.setdefault("total_volume", 0)
            market.setdefault("total_liquidity", 0)
            market.setdefault("end_date", datetime.now().isoformat())

            # Add outcomes if not present
            if "outcomes" not in market or not market["outcomes"]:
                import random

                yes_price = random.uniform(0.2, 0.8)
                no_price = 1.0 - yes_price
                market["outcomes"] = [
                    {"outcome": "yes", "price": yes_price},
                    {"outcome": "no", "price": no_price},
                ]

            if market.get("status") == "active":
                enhanced_markets.append(market)

        return enhanced_markets

    except Exception as e:
        print(f"Error fetching real polymarket data: {e}")
        # Return empty list instead of raising exception for optional data
        return []


def get_sample_polymarket_data() -> List[Dict[str, Any]]:
    """Get sample polymarket data for testing when real API is not available."""
    import random
    from datetime import datetime, timedelta

    sample_markets = [
        {
            "id": "bitcoin_100k_2024",
            "title": "Will Bitcoin reach $100,000 by end of 2024?",
            "category": "crypto",
            "description": "Bitcoin price prediction for end of 2024",
            "end_date": (datetime.now() + timedelta(days=90)).isoformat(),
            "status": "active",
            "total_volume": random.uniform(80000, 800000),
            "total_liquidity": random.uniform(30000, 150000),
            "outcomes": [
                {"outcome": "yes", "price": random.uniform(0.25, 0.45)},
                {"outcome": "no", "price": random.uniform(0.55, 0.75)},
            ],
        },
        {
            "id": "us_election_2024",
            "title": "Will Democrats win the 2024 US Presidential Election?",
            "category": "politics",
            "description": "2024 US Presidential Election outcome prediction",
            "end_date": (datetime.now() + timedelta(days=60)).isoformat(),
            "status": "active",
            "total_volume": random.uniform(200000, 2000000),
            "total_liquidity": random.uniform(100000, 500000),
            "outcomes": [
                {"outcome": "yes", "price": random.uniform(0.45, 0.55)},
                {"outcome": "no", "price": random.uniform(0.45, 0.55)},
            ],
        },
        {
            "id": "agi_breakthrough_2025",
            "title": "Will AGI be achieved by major tech company by 2025?",
            "category": "tech",
            "description": "Artificial General Intelligence breakthrough prediction",
            "end_date": (datetime.now() + timedelta(days=365)).isoformat(),
            "status": "active",
            "total_volume": random.uniform(50000, 500000),
            "total_liquidity": random.uniform(25000, 125000),
            "outcomes": [
                {"outcome": "yes", "price": random.uniform(0.15, 0.35)},
                {"outcome": "no", "price": random.uniform(0.65, 0.85)},
            ],
        },
    ]

    # Normalize prices so they sum to ~1
    for market in sample_markets:
        outcomes = market["outcomes"]
        if isinstance(outcomes, list) and len(outcomes) == 2:
            total_price = sum(
                o["price"] for o in outcomes if isinstance(o, dict) and "price" in o
            )
            if total_price > 0:
                for outcome in outcomes:
                    if isinstance(outcome, dict) and "price" in outcome:
                        outcome["price"] = outcome["price"] / total_price

    return sample_markets

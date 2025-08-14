from app.schemas import (
    ModelStatus,
    NewsCategory,
    NewsImpact,
    NewsItem,
    Trade,
    TradeType,
    TradingModel,
)

# Import trading actions management
from app.trading_actions import get_trading_actions


def get_real_models_data() -> list[TradingModel]:
    """Get real LLM model performance data from actual trading predictions."""
    # These are the different LLM models that can be used in trading_bench.model_wrapper
    # Each model corresponds to different LLM providers and models
    # Performance gets calculated from their actual predictions vs market outcomes
    llm_models = [
        TradingModel(
            id="claude-3.5-sonnet",
            name="Claude 3.5 Sonnet",
            performance=0.0,  # % of correct predictions
            accuracy=0.0,  # Same as performance
            trades=0,  # Number of predictions made via run_trade()
            profit=0.0,  # Total profit from eval() results
            status=ModelStatus.INACTIVE,  # ACTIVE when making predictions
        ),
        TradingModel(
            id="gpt-4",
            name="GPT-4",
            performance=0.0,
            accuracy=0.0,
            trades=0,
            profit=0.0,
            status=ModelStatus.INACTIVE,
        ),
        TradingModel(
            id="gemini-1.5-pro",
            name="Gemini 1.5 Pro",
            performance=0.0,
            accuracy=0.0,
            trades=0,
            profit=0.0,
            status=ModelStatus.INACTIVE,
        ),
        TradingModel(
            id="claude-4-haiku",
            name="Claude 4 Haiku",
            performance=0.0,
            accuracy=0.0,
            trades=0,
            profit=0.0,
            status=ModelStatus.INACTIVE,
        ),
    ]
    return llm_models


def get_real_trades_data(ticker: str = "NVDA", days: int = 7) -> list[Trade]:
    """Get real trading data by fetching stock prices."""
    import os
    import sys
    from datetime import datetime, timedelta

    # Add trading_bench to path
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    sys.path.insert(0, project_root)

    try:
        from trading_bench.fetchers.stock_fetcher import fetch_stock_data

        # Calculate date range
        end_date = datetime.now() - timedelta(days=1)  # Yesterday
        start_date = end_date - timedelta(days=days)

        # Fetch real stock data
        price_data = fetch_stock_data(
            ticker=ticker,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=(end_date + timedelta(days=1)).strftime("%Y-%m-%d"),
            resolution="D",
        )
        if not price_data:
            print("No price data available for the specified ticker and date range.")
            return []

        # Convert price data to trade records
        trades = []
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
        return []


def get_real_news_data(query: str = "stock market", days: int = 7) -> list[NewsItem]:
    """Get real news data from Google News."""
    import os
    import sys
    from datetime import datetime, timedelta

    # Add trading_bench to path
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    sys.path.insert(0, project_root)

    try:
        from trading_bench.fetchers.news_fetcher import fetch_news_data

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Fetch real news data
        raw_news = fetch_news_data(
            query=query,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            max_pages=3,
        )

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

                # Determine category based on keywords
                if any(
                    word in title_lower or word in snippet_lower
                    for word in ["fed", "federal", "rate", "inflation", "economy"]
                ):
                    category = NewsCategory.ECONOMIC
                elif any(
                    word in title_lower or word in snippet_lower
                    for word in [
                        "tech",
                        "ai",
                        "software",
                        "apple",
                        "google",
                        "microsoft",
                    ]
                ):
                    category = NewsCategory.TECH
                elif any(
                    word in title_lower or word in snippet_lower
                    for word in ["earnings", "company", "ceo", "revenue"]
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
                )
                news_items.append(news_item)

            except Exception as e:
                print(f"Error processing article {i}: {e}")
                continue

        return news_items

    except Exception as e:
        print(f"Error fetching real news: {e}")
        return []


def get_real_social_data(
    category: str = "all", query: str = None, days: int = 7
) -> list[dict]:
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

    # Add trading_bench to path
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    sys.path.insert(0, project_root)

    try:
        from trading_bench.fetchers.reddit_fetcher import (
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
                elif reddit_category == "options":
                    post_category = "options"
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
        return []


def get_real_system_log_data(
    agent_type: str = None, status: str = None, limit: int = 100, hours: int = 24
) -> list[dict]:
    """Get trading actions from system logs - ONLY trading decisions, not data fetching."""
    # Get trading actions using the new system - NO SAMPLE DATA
    actions = get_trading_actions(
        agent_type=agent_type, status=status, limit=limit, hours=hours
    )
    return actions

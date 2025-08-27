"""
Multi-Asset Trading System Integration using existing .run() methods from live_trade_bench

This module uses the native TradingSystem and PolymarketTradingSystem classes
with their .run() methods, following the same patterns as the demo scripts.
"""

import logging
import os
import sys
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import pytz  # type: ignore[import-untyped]

# Add live_trade_bench to path before any runtime imports
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, project_root)

# Type-only imports to avoid E402 while keeping annotations
if TYPE_CHECKING:  # pragma: no cover - type checking only
    pass

logger = logging.getLogger(__name__)


def is_market_hours() -> bool:
    """Check if current time is during stock market hours (9:30 AM - 4:00 PM ET, weekdays only)"""
    # Get current time in Eastern timezone
    et_tz = pytz.timezone("US/Eastern")
    current_et = datetime.now(et_tz)

    # Check if it's a weekday (Monday=0, Sunday=6)
    if current_et.weekday() >= 5:  # Saturday or Sunday
        return False

    # Check if it's within market hours (9:30 AM - 4:00 PM ET)
    market_open = current_et.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = current_et.replace(hour=16, minute=0, second=0, microsecond=0)

    return market_open <= current_et <= market_close


def get_market_status() -> Dict[str, Any]:
    """Get detailed market status information"""
    et_tz = pytz.timezone("US/Eastern")
    current_et = datetime.now(et_tz)

    is_weekday = current_et.weekday() < 5
    is_open = is_market_hours()

    # Calculate next market open
    if (
        is_weekday
        and current_et.hour < 9
        or (current_et.hour == 9 and current_et.minute < 30)
    ):
        # Market opens today
        next_open = current_et.replace(hour=9, minute=30, second=0, microsecond=0)
    else:
        # Market opens next weekday
        days_ahead = 1
        while True:
            next_day = current_et + timedelta(days=days_ahead)
            if next_day.weekday() < 5:  # Weekday
                next_open = next_day.replace(hour=9, minute=30, second=0, microsecond=0)
                break
            days_ahead += 1

    # Calculate next market close
    if is_open:
        next_close = current_et.replace(hour=16, minute=0, second=0, microsecond=0)
    else:
        next_close = next_open.replace(hour=16, minute=0, second=0, microsecond=0)

    return {
        "is_open": is_open,
        "is_weekday": is_weekday,
        "current_time_et": current_et.isoformat(),
        "next_open": next_open.isoformat(),
        "next_close": next_close.isoformat(),
        "timezone": "US/Eastern",
    }


class MultiAssetTradingSystem:
    """
    Multi-asset trading system that uses the native .run() methods from
    both StockPortfolioSystem and PolymarketPortfolioSystem for portfolio-based trading
    """

    def __init__(self) -> None:
        # Import the native portfolio systems using factory functions
        from live_trade_bench import (
            create_polymarket_portfolio_system,
            create_stock_portfolio_system,
        )

        # Create the native portfolio systems using factory functions
        self.stock_system = create_stock_portfolio_system()
        self.polymarket_system = create_polymarket_portfolio_system()

        # System control
        self.system_running = False
        self.trading_thread: Optional[threading.Thread] = None

        # Trading configuration matching demo patterns
        self.cycle_interval = 30 * 60  # 30 minutes between cycles
        self.stock_initial_cash = 1000.0
        self.polymarket_initial_cash = 500.0

        # Model configurations for multiple LLM models
        self.models_config = [
            {
                "id": "claude-3.7-sonnet",
                "name": "Claude 3.7 Sonnet",
                "llm_model": "claude-3-7-sonnet-20250219",
            },
            {
                "id": "gpt-5",
                "name": "GPT-5",
                "llm_model": "openai/gpt-5",
            },
            {
                "id": "gpt-4o",
                "name": "GPT-4o",
                "llm_model": "openai/gpt-4o",
            },
            {
                "id": "gemini-2.5-flash",
                "name": "Gemini 2.5 Flash",
                "llm_model": "gemini/gemini-2.5-flash",
            },
            {
                "id": "claude-4-sonnet",
                "name": "Claude 4 Sonnet",
                "llm_model": "claude-sonnet-4-20250514",
            },
            {
                "id": "grok-4",
                "name": "Grok 4",
                "llm_model": "xai/grok-4-0709",
            },
            {
                "id": "deepseek-chat",
                "name": "Deepseek V3 (Chat)",
                "llm_model": "deepseek/deepseek-chat",
            },
        ]

        # Model activation controls
        self.active_stock_models: Dict[str, bool] = {}
        self.active_polymarket_models: Dict[str, bool] = {}

        # Performance tracking
        self.last_cycle_time: Optional[datetime] = None
        self.next_cycle_time: Optional[datetime] = None
        self.execution_stats = {
            "total_cycles": 0,
            "successful_cycles": 0,
            "failed_cycles": 0,
            "total_stock_actions": 0,
            "total_polymarket_actions": 0,
            "successful_stock_actions": 0,
            "successful_polymarket_actions": 0,
            "failed_stock_actions": 0,
            "failed_polymarket_actions": 0,
        }

        # Unified trading history from both systems
        self.trading_history: List[Dict[str, Any]] = []

        # Background news cache
        self.cached_news: List[Dict[str, Any]] = []
        self.news_last_updated: Optional[datetime] = None
        self.news_update_interval = 60 * 60  # 1 hour in seconds

        # Background social media cache
        self.cached_social: List[Dict[str, Any]] = []
        self.social_last_updated: Optional[datetime] = None
        self.social_update_interval = 60 * 60  # 1 hour in seconds

        # Execution logs
        self.execution_logs: List[Dict[str, Any]] = []
        self.max_log_entries = 1000

        # System startup time
        self.start_time = datetime.now(timezone.utc)

        # Initialize models in both systems
        self._initialize_models()

        # Initialize news cache
        self._update_news_cache()

        # Initialize social media cache
        self._update_social_cache()

        logger.info(
            "Multi-asset portfolio system initialized using native .run() methods"
        )

    @property
    def stock_agents(self) -> List[str]:
        """Return base model ids for stock agents (compat shim)."""
        return list(self.active_stock_models.keys())

    @property
    def polymarket_agents(self) -> List[str]:
        """Return base model ids for polymarket agents (compat shim)."""
        return list(self.active_polymarket_models.keys())

    def _initialize_models(self) -> None:
        """Initialize agents in both native portfolio systems"""

        # Initialize stock agents using native StockPortfolioSystem.add_agent()
        for model_config in self.models_config:
            model_id = model_config["id"]
            model_name = model_config["name"]
            llm_model = model_config["llm_model"]

            # Add agent to stock portfolio system using native method
            self.stock_system.add_agent(
                name=f"{model_name} (Stock)",
                initial_cash=self.stock_initial_cash,
                model_name=llm_model,
            )

            # Add agent to polymarket portfolio system using native method
            self.polymarket_system.add_agent(
                name=f"{model_name} (Polymarket)",
                initial_cash=self.polymarket_initial_cash,
                model_name=llm_model,
            )

            # Track activation status
            self.active_stock_models[model_id] = True
            self.active_polymarket_models[model_id] = True

            logger.info(
                f"Initialized {model_name} in both stock and polymarket systems"
            )

    def _update_news_cache(self) -> None:
        """Update the news cache in background"""
        try:
            logger.info("Updating background news cache")

            # Import news fetcher directly to avoid circular imports
            from live_trade_bench import fetch_trending_stocks
            from live_trade_bench.fetchers.news_fetcher import fetch_news_data

            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)

            raw_news = []
            try:
                # Get trending stocks for news queries
                trending_stocks = fetch_trending_stocks(limit=5)

                for ticker in trending_stocks[:3]:  # Limit to 3 stocks
                    stock_query = f"{ticker} stock"
                    try:
                        stock_news = fetch_news_data(
                            query=stock_query,
                            start_date=start_date.strftime("%Y-%m-%d"),
                            end_date=end_date.strftime("%Y-%m-%d"),
                            max_pages=1,
                        )
                        raw_news.extend(stock_news[:5])  # Limit to 5 articles per stock
                    except Exception as e:
                        logger.warning(f"Error fetching news for {ticker}: {e}")
                        continue
            except Exception as e:
                logger.warning(f"Error fetching trending stocks for news: {e}")

            # Transform raw news to dict format for JSON serialization
            self.cached_news = []
            for i, article in enumerate(raw_news[:15]):  # Limit to 15 articles total
                try:
                    self.cached_news.append(
                        {
                            "id": str(i + 1),
                            "title": article.get("title", "No title"),
                            "summary": article.get("snippet", "No summary"),
                            "source": article.get("source", "Unknown"),
                            "published_at": datetime.now().isoformat(),
                            "impact": "medium",
                            "category": "market",
                            "url": article.get("link", "#"),
                            "stock_symbol": None,
                        }
                    )
                except Exception as e:
                    logger.warning(f"Error processing news article {i}: {e}")
                    continue

            self.news_last_updated = datetime.now(timezone.utc)
            logger.info(f"News cache updated with {len(self.cached_news)} articles")

        except Exception as e:
            logger.error(f"Error updating news cache: {e}")
            # Don't clear cache on error, keep previous data

    def get_cached_news(self) -> List[Dict[str, Any]]:
        """Get cached news data"""
        # Check if cache needs refresh
        if (
            not self.news_last_updated
            or (datetime.now(timezone.utc) - self.news_last_updated).total_seconds()
            > self.news_update_interval
        ):
            self._update_news_cache()

        return self.cached_news

    def _should_update_news(self) -> bool:
        """Check if news cache should be updated"""
        if not self.news_last_updated:
            return True

        time_since_update = (
            datetime.now(timezone.utc) - self.news_last_updated
        ).total_seconds()
        return time_since_update >= self.news_update_interval

    def _update_social_cache(self) -> None:
        """Update the social media cache in background"""
        try:
            # Import here to avoid circular imports
            from live_trade_bench.fetchers.reddit_fetcher import RedditFetcher

            logger.info("Updating background social media cache")

            # Use RedditFetcher directly
            reddit_fetcher = RedditFetcher()

            # Fetch from multiple categories
            categories = ["stocks", "investing", "wallstreetbets"]
            all_posts = []

            for category in categories:
                try:
                    posts = reddit_fetcher.fetch(
                        category=category,
                        query=None,
                        max_limit=20,  # Limit posts per category
                        time_filter="day",
                    )
                    all_posts.extend(posts)
                except Exception as e:
                    logger.warning(f"Error fetching from {category}: {e}")
                    continue

            # Transform to dict format for JSON serialization
            self.cached_social = []
            for i, post in enumerate(all_posts):
                try:
                    self.cached_social.append(
                        {
                            "id": f"social_{i}_{int(datetime.now().timestamp())}",
                            "title": post.get("title", "No title"),
                            "content": post.get("selftext", post.get("content", "")),
                            "author": post.get("author", "Unknown"),
                            "subreddit": post.get("subreddit", "Unknown"),
                            "score": post.get("score", 0),
                            "num_comments": post.get("num_comments", 0),
                            "created_utc": post.get(
                                "created_utc", datetime.now().timestamp()
                            ),
                            "url": post.get("url", ""),
                            "sentiment": "neutral",  # Default sentiment
                            "platform": "reddit",
                        }
                    )
                except Exception as e:
                    logger.warning(f"Error processing social post: {e}")
                    continue

            self.social_last_updated = datetime.now(timezone.utc)
            logger.info(f"Social cache updated with {len(self.cached_social)} posts")

        except Exception as e:
            logger.error(f"Error updating social cache: {e}")
            # Don't clear cache on error, keep previous data

    def get_cached_social(self) -> List[Dict[str, Any]]:
        """Get cached social media data"""
        # Check if cache needs refresh
        if (
            not self.social_last_updated
            or (datetime.now(timezone.utc) - self.social_last_updated).total_seconds()
            > self.social_update_interval
        ):
            self._update_social_cache()

        return self.cached_social

    def _should_update_social(self) -> bool:
        """Check if social media cache should be updated"""
        if not self.social_last_updated:
            return True

        time_since_update = (
            datetime.now(timezone.utc) - self.social_last_updated
        ).total_seconds()
        return time_since_update >= self.social_update_interval

    def get_model_data(self) -> List[Dict[str, Any]]:
        """Get current model performance data from both systems"""
        models_data = []

        # Get stock model data
        for model_id, model_config in zip(
            self.active_stock_models.keys(), self.models_config
        ):
            agent_name = f"{model_config['name']} (Stock)"
            if agent_name in self.stock_system.agents:
                stock_agent: Any = self.stock_system.agents[agent_name]
                stock_account: Any = self.stock_system.accounts[agent_name]

                try:
                    stock_evaluation = stock_account.evaluate()
                    stock_portfolio_summary = stock_evaluation["portfolio_summary"]

                    stock_model_data = {
                        "id": f"{model_id}_stock",
                        "name": stock_agent.name,
                        "category": "stock",
                        "performance": stock_portfolio_summary["return_pct"],
                        "accuracy": self._calculate_stock_accuracy(stock_account),
                        "trades": len(stock_account.transactions),
                        "profit": stock_portfolio_summary["total_return"],
                        "status": (
                            "active"
                            if self.active_stock_models.get(model_id, True)
                            else "inactive"
                        ),
                        "total_value": stock_portfolio_summary["total_value"],
                        "cash_balance": stock_account.cash_balance,
                        "active_positions": len(stock_account.get_active_positions()),
                        "is_activated": self.active_stock_models.get(model_id, True),
                        "recent_performance": self._get_recent_performance(
                            f"{model_id}_stock"
                        ),
                        "llm_available": stock_agent.available,
                    }
                    models_data.append(stock_model_data)
                except Exception as e:
                    logger.error(f"Error getting stock data for {model_id}: {e}")

        # Get polymarket model data
        for model_id, model_config in zip(
            self.active_polymarket_models.keys(), self.models_config
        ):
            agent_name = f"{model_config['name']} (Polymarket)"
            if agent_name in self.polymarket_system.agents:
                polymarket_agent: Any = self.polymarket_system.agents[agent_name]
                polymarket_account: Any = self.polymarket_system.accounts[agent_name]

                try:
                    polymarket_evaluation = polymarket_account.evaluate()
                    polymarket_portfolio_summary = polymarket_evaluation[
                        "portfolio_summary"
                    ]

                    polymarket_model_data = {
                        "id": f"{model_id}_polymarket",
                        "name": polymarket_agent.name,
                        "category": "polymarket",
                        "performance": polymarket_portfolio_summary["return_pct"],
                        "accuracy": self._calculate_polymarket_accuracy(
                            polymarket_account
                        ),
                        "trades": len(polymarket_account.transactions),
                        "profit": polymarket_portfolio_summary["total_return"],
                        "status": (
                            "active"
                            if self.active_polymarket_models.get(model_id, True)
                            else "inactive"
                        ),
                        "total_value": polymarket_portfolio_summary["total_value"],
                        "cash_balance": polymarket_account.cash_balance,
                        "active_positions": len(
                            polymarket_account.get_active_positions()
                        ),
                        "is_activated": self.active_polymarket_models.get(
                            model_id, True
                        ),
                        "recent_performance": self._get_recent_performance(
                            f"{model_id}_polymarket"
                        ),
                        "llm_available": polymarket_agent.available,
                        "market_type": "prediction_markets",
                    }
                    models_data.append(polymarket_model_data)
                except Exception as e:
                    logger.error(f"Error getting polymarket data for {model_id}: {e}")

        return models_data

    def _calculate_stock_accuracy(self, account: Any) -> float:
        """Calculate stock trading accuracy"""
        total_trades = len(account.transactions)
        if total_trades == 0:
            return 0.0

        try:
            profitable_trades = 0
            for transaction in account.transactions:
                if transaction.action == "sell":
                    if account.evaluate()["portfolio_summary"]["return_pct"] > 0:
                        profitable_trades += 1
            return (profitable_trades / total_trades) * 100 if total_trades > 0 else 0.0
        except Exception:
            return 0.0

    def _calculate_polymarket_accuracy(self, account: Any) -> float:
        """Calculate polymarket prediction accuracy"""
        total_trades = len(account.transactions)
        if total_trades == 0:
            return 0.0

        # Simplified accuracy calculation for polymarket
        try:
            return (total_trades // 2) / total_trades * 100 if total_trades > 0 else 0.0
        except Exception:
            return 0.0

    def _get_recent_performance(self, model_full_id: str) -> Dict[str, Any]:
        """Get recent performance metrics for a model"""
        daily_actions = self.get_recent_actions(model_full_id, hours=24)
        weekly_actions = self.get_recent_actions(model_full_id, hours=168)

        successful_daily = len(
            [a for a in daily_actions if a.get("status") == "executed"]
        )
        total_daily = len(daily_actions)
        recent_win_rate = (successful_daily / max(total_daily, 1)) * 100

        return {
            "daily_actions": len(daily_actions),
            "weekly_actions": len(weekly_actions),
            "recent_win_rate": recent_win_rate,
            "last_action_time": (
                daily_actions[0]["timestamp"] if daily_actions else None
            ),
        }

    def get_recent_actions(
        self, model_id: Optional[str] = None, hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Get recent trading actions from unified history"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        actions = []
        for action in self.trading_history:
            try:
                action_time = datetime.fromisoformat(action["timestamp"])
                if action_time >= cutoff_time:
                    if model_id is None or action["agent_id"] == model_id:
                        actions.append(action)
            except Exception:
                continue

        return sorted(actions, key=lambda x: x["timestamp"], reverse=True)

    def get_market_status(self) -> Dict[str, Any]:
        """Get current market status for frontend display"""
        return get_market_status()

    def get_stock_tickers(self) -> List[str]:
        """Get actual stock tickers being traded by the stock system"""
        try:
            if hasattr(self.stock_system, "universe") and self.stock_system.universe:
                return list(self.stock_system.universe)
            else:
                # Fallback: fetch trending stocks directly
                from live_trade_bench import fetch_trending_stocks

                trending_stocks = fetch_trending_stocks(limit=10)
                # fetch_trending_stocks may return either a list of ticker strings
                # or a list of dicts with 'ticker' keys depending on implementation.
                if not trending_stocks:
                    return []
                first = trending_stocks[0]
                if isinstance(first, str):
                    return trending_stocks
                elif isinstance(first, dict):
                    return [
                        s.get("ticker", "") for s in trending_stocks if s.get("ticker")
                    ]
                else:
                    return []
        except Exception as e:
            logger.warning(f"Could not get stock tickers: {e}")
            # Ultimate fallback to ensure API doesn't break
            return ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA"]

    def activate_model(self, model_id: str, category: Optional[str] = None) -> bool:
        """Activate a trading model for specific category or both"""
        base_model_id = model_id.replace("_stock", "").replace("_polymarket", "")

        if category == "stock" or model_id.endswith("_stock"):
            if base_model_id in self.active_stock_models:
                self.active_stock_models[base_model_id] = True
                logger.info(f"Activated stock model: {base_model_id}")
                return True
        elif category == "polymarket" or model_id.endswith("_polymarket"):
            if base_model_id in self.active_polymarket_models:
                self.active_polymarket_models[base_model_id] = True
                logger.info(f"Activated polymarket model: {base_model_id}")
                return True
        else:
            # Activate both if no specific category
            success = False
            if base_model_id in self.active_stock_models:
                self.active_stock_models[base_model_id] = True
                success = True
            if base_model_id in self.active_polymarket_models:
                self.active_polymarket_models[base_model_id] = True
                success = True
            return success

        return False

    def deactivate_model(self, model_id: str, category: Optional[str] = None) -> bool:
        """Deactivate a trading model for specific category or both"""
        base_model_id = model_id.replace("_stock", "").replace("_polymarket", "")

        if category == "stock" or model_id.endswith("_stock"):
            if base_model_id in self.active_stock_models:
                self.active_stock_models[base_model_id] = False
                logger.info(f"Deactivated stock model: {base_model_id}")
                return True
        elif category == "polymarket" or model_id.endswith("_polymarket"):
            if base_model_id in self.active_polymarket_models:
                self.active_polymarket_models[base_model_id] = False
                logger.info(f"Deactivated polymarket model: {base_model_id}")
                return True
        else:
            # Deactivate both if no specific category
            success = False
            if base_model_id in self.active_stock_models:
                self.active_stock_models[base_model_id] = False
                success = True
            if base_model_id in self.active_polymarket_models:
                self.active_polymarket_models[base_model_id] = False
                success = True
            return success

        return False

    def set_cycle_interval(self, minutes: int) -> bool:
        """Set trading cycle interval in minutes"""
        if minutes >= 1:
            self.cycle_interval = minutes * 60
            logger.info(f"Set cycle interval to {minutes} minutes")
            return True
        return False

    def run_trading_cycle(self) -> None:
        """Run one trading cycle using the native .run() methods"""
        cycle_start_time = datetime.now(timezone.utc)
        self.execution_stats["total_cycles"] += 1

        try:
            logger.info(
                f"Starting native .run() trading cycle #{self.execution_stats['total_cycles']}"
            )

            # Use native .run() methods in separate threads to run concurrently
            stock_thread = threading.Thread(
                target=self._run_stock_cycle_native, daemon=True
            )
            polymarket_thread = threading.Thread(
                target=self._run_polymarket_cycle_native, daemon=True
            )

            # Start both cycles concurrently
            stock_thread.start()
            polymarket_thread.start()

            # Wait for both to complete (with timeout)
            stock_thread.join(timeout=120)  # 2 minute timeout
            polymarket_thread.join(timeout=120)

            # Update cycle tracking
            self.last_cycle_time = cycle_start_time
            self.next_cycle_time = cycle_start_time + timedelta(
                seconds=self.cycle_interval
            )
            self.execution_stats["successful_cycles"] += 1

            cycle_duration = (
                datetime.now(timezone.utc) - cycle_start_time
            ).total_seconds()
            logger.info(f"Native .run() cycle completed in {cycle_duration:.1f}s")

            # Log cycle execution
            self._add_execution_log(
                "cycle_completed",
                {
                    "cycle_number": self.execution_stats["total_cycles"],
                    "duration_seconds": cycle_duration,
                    "method": "native_run",
                },
            )

        except Exception as e:
            logger.error(f"Error in native .run() trading cycle: {e}")
            self.execution_stats["failed_cycles"] += 1

            self._add_execution_log(
                "cycle_failed",
                {
                    "cycle_number": self.execution_stats["total_cycles"],
                    "error": str(e),
                    "duration_seconds": (
                        datetime.now(timezone.utc) - cycle_start_time
                    ).total_seconds(),
                },
            )

    def _run_stock_cycle_native(self) -> None:
        """Run stock cycle using native StockPortfolioSystem.run() - adapted for backend service"""
        try:
            # Check if market is open before running stock trading
            if not is_market_hours():
                market_status = get_market_status()
                logger.info(
                    f"Stock market is closed. Market will open at {market_status['next_open']} ET. Skipping stock trading cycle."
                )
                return

            logger.info(
                "Running stock system using native .run() method (market is open)"
            )

            # For backend service: run a short burst
            # This gets called repeatedly by our background loop (every 30 min)
            # So we run for 2 minutes each time with 30 second intervals
            self.stock_system.run(
                duration_minutes=2,  # Short burst duration per call
                interval=30,  # 30 seconds between cycles within this burst
            )
            logger.info("Stock system .run() completed")
        except Exception as e:
            logger.error(f"Error in stock system .run(): {e}")

    def _run_polymarket_cycle_native(self) -> None:
        """Run polymarket cycle using native PolymarketPortfolioSystem.run() - portfolio-based trading"""
        try:
            logger.info("Running polymarket system using native .run() method")
            # Short burst for backend service
            self.polymarket_system.run(
                duration_minutes=2,  # Short burst duration
                interval=60,  # 1 minute between cycles
            )
            logger.info("Polymarket system .run() completed")
        except Exception as e:
            logger.error(f"Error in polymarket system .run(): {e}")

    def get_portfolio(self, model_id: str) -> Dict[str, Any]:
        """Get portfolio data for a specific model"""
        if model_id.endswith("_stock"):
            base_model_id = model_id.replace("_stock", "")
            model_config = next(
                (m for m in self.models_config if m["id"] == base_model_id), None
            )
            if model_config:
                agent_name = f"{model_config['name']} (Stock)"
                if agent_name in self.stock_system.agents:
                    agent_stock: Any = self.stock_system.agents[agent_name]
                    account_stock: Any = self.stock_system.accounts[agent_name]
                    evaluation = account_stock.evaluate()

                # Extract holdings and detailed position info for frontend compatibility
                holdings = {}
                positions = {}

                # Get active positions from account
                try:
                    active_positions = account_stock.get_active_positions()
                    for ticker, position in active_positions.items():
                        holdings[ticker] = position.quantity
                        positions[ticker] = {
                            "current_price": getattr(position, "current_price", 0.0),
                            "avg_price": getattr(position, "avg_price", 0.0),
                            "unrealized_pnl": getattr(position, "unrealized_pnl", 0.0),
                            "current_value": position.quantity
                            * getattr(position, "current_price", 0.0),
                        }
                except Exception as e:
                    logger.warning(f"Error getting positions for {model_id}: {e}")

                return {
                    "model_id": model_id,
                    "model_name": agent_stock.name,
                    "category": "stock",
                    "cash": account_stock.cash_balance,
                    "total_value": evaluation["portfolio_summary"]["total_value"],
                    "return_pct": evaluation["portfolio_summary"]["return_pct"],
                    "holdings": holdings,
                    "positions": positions,
                    "unrealized_pnl": evaluation["portfolio_summary"].get(
                        "unrealized_pnl", 0.0
                    ),
                    "market_data_available": True,  # Assume market data is available
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                }

        elif model_id.endswith("_polymarket"):
            base_model_id = model_id.replace("_polymarket", "")
            model_config = next(
                (m for m in self.models_config if m["id"] == base_model_id), None
            )
            if model_config:
                agent_name = f"{model_config['name']} (Polymarket)"
                if agent_name in self.polymarket_system.agents:
                    agent_poly: Any = self.polymarket_system.agents[agent_name]
                    account_poly: Any = self.polymarket_system.accounts[agent_name]
                    evaluation = account_poly.evaluate()

                # Extract holdings and detailed position info for polymarket
                holdings = {}
                positions = {}

                # Get active positions from polymarket account
                try:
                    active_positions = account_poly.get_active_positions()
                    for market_id, position in active_positions.items():
                        holdings[market_id] = position.quantity
                        positions[market_id] = {
                            "current_price": getattr(position, "current_price", 0.0),
                            "avg_price": getattr(position, "avg_price", 0.0),
                            "unrealized_pnl": getattr(position, "unrealized_pnl", 0.0),
                            "current_value": position.quantity
                            * getattr(position, "current_price", 0.0),
                            "outcome": getattr(position, "outcome", "unknown"),
                        }
                except Exception as e:
                    logger.warning(
                        f"Error getting polymarket positions for {model_id}: {e}"
                    )

                return {
                    "model_id": model_id,
                    "model_name": agent_poly.name,
                    "category": "polymarket",
                    "cash": account_poly.cash_balance,
                    "total_value": evaluation["portfolio_summary"]["total_value"],
                    "return_pct": evaluation["portfolio_summary"]["return_pct"],
                    "holdings": holdings,
                    "positions": positions,
                    "unrealized_pnl": evaluation["portfolio_summary"].get(
                        "unrealized_pnl", 0.0
                    ),
                    "market_data_available": True,  # Assume market data is available
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                }

        raise ValueError(f"Invalid model_id format: {model_id}")

    def _get_realtime_portfolio_data(self, model_id: str) -> Dict[str, Any]:
        """Get real-time portfolio data using market fetchers"""
        try:
            # Import fetchers for real-time data
            from live_trade_bench.fetchers.stock_fetcher import StockFetcher

            # Get current portfolio
            portfolio_data = self.get_portfolio(model_id)
            holdings = portfolio_data.get("holdings", {})

            if not holdings:
                return {}

            # Get real-time prices for holdings
            stock_fetcher = StockFetcher()
            realtime_prices = {}
            total_realtime_value = portfolio_data.get("cash", 0)

            for ticker, quantity in holdings.items():
                try:
                    # Get current price for ticker using stock data fetch
                    from datetime import datetime, timedelta

                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=1)

                    price_data = stock_fetcher.fetch_stock_data(
                        ticker=ticker,
                        start_date=start_date.strftime("%Y-%m-%d"),
                        end_date=end_date.strftime("%Y-%m-%d"),
                        interval="1d",
                    )

                    if (
                        price_data
                        and hasattr(price_data, "iloc")
                        and len(price_data) > 0
                    ):
                        # Get the most recent price from DataFrame
                        current_price = price_data.iloc[-1]["close"]
                        realtime_prices[ticker] = current_price
                        total_realtime_value += quantity * current_price
                    elif isinstance(price_data, dict) and price_data:
                        # Handle dict format
                        latest_date = max(price_data.keys())
                        current_price = price_data[latest_date].get("close", 0)
                        if current_price > 0:
                            realtime_prices[ticker] = current_price
                            total_realtime_value += quantity * current_price
                except Exception as e:
                    logger.warning(f"Error getting real-time price for {ticker}: {e}")
                    continue

            # Calculate real-time metrics
            initial_value = (
                self.stock_initial_cash
                if model_id.endswith("_stock")
                else self.polymarket_initial_cash
            )
            realtime_return_pct = (
                ((total_realtime_value - initial_value) / initial_value * 100)
                if initial_value > 0
                else 0
            )

            # Calculate real-time unrealized P&L
            base_unrealized_pnl = portfolio_data.get("unrealized_pnl", 0)
            realtime_unrealized_pnl = total_realtime_value - portfolio_data.get(
                "total_value", initial_value
            )

            return {
                "total_value": total_realtime_value,
                "return_pct": realtime_return_pct,
                "unrealized_pnl": base_unrealized_pnl + realtime_unrealized_pnl,
                "realtime_prices": realtime_prices,
            }

        except Exception as e:
            logger.error(f"Error getting real-time portfolio data for {model_id}: {e}")
            return {}

    def get_portfolio_history(
        self, model_id: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get portfolio history for area chart visualization"""
        try:
            # Get historical trading actions for this model
            model_actions = [
                action
                for action in self.trading_history
                if action.get("agent_id") == model_id
                or action.get("model_id") == model_id
            ]

            if not model_actions:
                # Return single point with current portfolio state
                current_portfolio = self.get_portfolio(model_id)
                return [
                    {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "holdings": current_portfolio.get("holdings", {}),
                        "prices": {
                            ticker: 100.0
                            for ticker in current_portfolio.get("holdings", {}).keys()
                        },
                        "cash": current_portfolio.get("cash", 1000),
                        "totalValue": current_portfolio.get("total_value", 1000),
                    }
                ]

            # Build portfolio history from actions
            portfolio_history = []
            current_holdings = {}
            initial_cash = (
                self.stock_initial_cash
                if model_id.endswith("_stock")
                else self.polymarket_initial_cash
            )
            current_cash = initial_cash

            for action in model_actions[-limit:]:
                try:
                    action_type = action.get("action", "")
                    symbol = action.get("symbol", "")
                    quantity = action.get("quantity", 0)
                    price = action.get("price", 0)

                    if action_type == "BUY" and symbol:
                        current_holdings[symbol] = (
                            current_holdings.get(symbol, 0) + quantity
                        )
                        current_cash -= quantity * price
                    elif action_type == "SELL" and symbol:
                        current_holdings[symbol] = max(
                            0, current_holdings.get(symbol, 0) - quantity
                        )
                        current_cash += quantity * price
                        if current_holdings[symbol] == 0:
                            del current_holdings[symbol]
                    elif action_type == "REBALANCE":
                        # Handle portfolio rebalancing
                        if "holdings" in action:
                            current_holdings = action["holdings"].copy()
                        if "cash_balance" in action:
                            current_cash = action["cash_balance"]

                    # Calculate prices and total value
                    prices = {}
                    total_holdings_value = 0

                    for ticker, holding_qty in current_holdings.items():
                        ticker_price = action.get("prices", {}).get(
                            ticker, price if ticker == symbol else 100
                        )
                        prices[ticker] = ticker_price
                        total_holdings_value += holding_qty * ticker_price

                    total_value = current_cash + total_holdings_value

                    portfolio_history.append(
                        {
                            "timestamp": action.get(
                                "timestamp", datetime.now(timezone.utc).isoformat()
                            ),
                            "holdings": current_holdings.copy(),
                            "prices": prices,
                            "cash": current_cash,
                            "totalValue": total_value,
                        }
                    )

                except Exception as e:
                    logger.warning(f"Error processing action in portfolio history: {e}")
                    continue

            # If still no history, add current state
            if not portfolio_history:
                current_portfolio = self.get_portfolio(model_id)
                portfolio_history = [
                    {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "holdings": current_portfolio.get("holdings", {}),
                        "prices": {
                            ticker: 100.0
                            for ticker in current_portfolio.get("holdings", {}).keys()
                        },
                        "cash": current_portfolio.get("cash", initial_cash),
                        "totalValue": current_portfolio.get(
                            "total_value", initial_cash
                        ),
                    }
                ]

            return portfolio_history

        except Exception as e:
            logger.error(f"Error generating portfolio history for {model_id}: {e}")
            return []

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get comprehensive system performance metrics"""
        total_stock_value = 0.0
        total_polymarket_value = 0.0
        total_initial_stock = len(self.stock_system.agents) * self.stock_initial_cash
        total_initial_polymarket = (
            len(self.polymarket_system.agents) * self.polymarket_initial_cash
        )

        # Calculate total system performance from native portfolio systems
        for agent_name in self.stock_system.agents.keys():
            try:
                stock_account = self.stock_system.accounts[agent_name]
                evaluation = stock_account.evaluate()
                total_stock_value += evaluation["portfolio_summary"]["total_value"]
            except Exception:
                total_stock_value += self.stock_initial_cash

        for agent_name in self.polymarket_system.agents.keys():
            try:
                polymarket_account = self.polymarket_system.accounts[agent_name]
                evaluation = polymarket_account.evaluate()
                total_polymarket_value += evaluation["portfolio_summary"]["total_value"]
            except Exception:
                total_polymarket_value += self.polymarket_initial_cash

        total_value = total_stock_value + total_polymarket_value
        total_initial = total_initial_stock + total_initial_polymarket
        system_return_pct = (
            ((total_value - total_initial) / total_initial * 100)
            if total_initial > 0
            else 0.0
        )

        uptime_seconds = (datetime.now(timezone.utc) - self.start_time).total_seconds()

        return {
            "system_performance": {
                "total_portfolio_value": total_value,
                "stock_portfolio_value": total_stock_value,
                "polymarket_portfolio_value": total_polymarket_value,
                "total_initial_value": total_initial,
                "system_return_pct": system_return_pct,
                "uptime_seconds": uptime_seconds,
                "uptime_hours": uptime_seconds / 3600,
            },
            "execution_stats": self.execution_stats,
            "active_stock_models_count": len(
                [m for m, active in self.active_stock_models.items() if active]
            ),
            "active_polymarket_models_count": len(
                [m for m, active in self.active_polymarket_models.items() if active]
            ),
            "total_models_count": len(self.stock_system.agents)
            + len(self.polymarket_system.agents),
            "recent_logs_count": len(self.execution_logs),
            "success_rate": {
                "cycles": (
                    self.execution_stats["successful_cycles"]
                    / max(self.execution_stats["total_cycles"], 1)
                )
                * 100,
            },
            "portfolio_systems": {
                "stock_agents": len(self.stock_system.agents),
                "polymarket_agents": len(self.polymarket_system.agents),
                "using_portfolio_run": True,
            },
        }

    def _add_execution_log(self, event_type: str, data: Dict[str, Any]) -> None:
        """Add entry to execution logs"""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "data": data,
        }

        self.execution_logs.append(log_entry)

        # Keep only the last max_log_entries
        if len(self.execution_logs) > self.max_log_entries:
            self.execution_logs = self.execution_logs[-self.max_log_entries :]

    def get_execution_logs(
        self, limit: int = 100, event_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get recent execution logs"""
        logs = self.execution_logs

        if event_type:
            logs = [log for log in logs if log["event_type"] == event_type]

        return sorted(logs, key=lambda x: x["timestamp"], reverse=True)[:limit]

    def start_background_trading(self) -> None:
        """Start background trading thread using native .run() methods"""
        if self.system_running:
            logger.warning("Multi-asset trading system already running")
            return

        self.system_running = True
        self.trading_thread = threading.Thread(
            target=self._background_trading_loop, daemon=True
        )
        self.trading_thread.start()
        logger.info("Multi-asset portfolio system started using native .run() methods")

    def stop_background_trading(self) -> None:
        """Stop background trading"""
        self.system_running = False
        if self.trading_thread:
            self.trading_thread.join(timeout=5)
        logger.info("Multi-asset portfolio system stopped")

    def _background_trading_loop(self) -> None:
        """Background trading loop using native .run() methods"""
        logger.info(
            f"Multi-asset portfolio loop started using native .run() methods with {self.cycle_interval//60} minute intervals"
        )

        while self.system_running:
            try:
                # Check if any models are active
                active_stock_models = [
                    model_id
                    for model_id, active in self.active_stock_models.items()
                    if active
                ]
                active_polymarket_models = [
                    model_id
                    for model_id, active in self.active_polymarket_models.items()
                    if active
                ]

                if not active_stock_models and not active_polymarket_models:
                    logger.info("No active models - skipping trading cycle")
                else:
                    logger.info(
                        f"Running native .run() cycle with {len(active_stock_models)} stock models and {len(active_polymarket_models)} polymarket models"
                    )
                    self.run_trading_cycle()

                # Update news cache if needed
                if self._should_update_news():
                    self._update_news_cache()

                # Update social media cache if needed
                if self._should_update_social():
                    self._update_social_cache()

                # Update next cycle time
                self.next_cycle_time = datetime.now(timezone.utc) + timedelta(
                    seconds=self.cycle_interval
                )

                # Wait for next cycle
                wait_time = 0
                status_interval = 300  # 5 minutes

                while wait_time < self.cycle_interval and self.system_running:
                    time.sleep(min(60, self.cycle_interval - wait_time))
                    wait_time += 60

                    if wait_time % status_interval == 0 and self.system_running:
                        remaining_minutes = (self.cycle_interval - wait_time) // 60
                        logger.info(
                            f"Multi-asset portfolio system running using native .run() - next cycle in {remaining_minutes} minutes"
                        )

            except Exception as e:
                logger.error(f"Error in multi-asset trading loop: {e}")
                time.sleep(60)

        logger.info("Multi-asset portfolio loop stopped")


# Global multi-asset portfolio system instance
trading_system = MultiAssetTradingSystem()


def get_trading_system() -> MultiAssetTradingSystem:
    """Get the global multi-asset portfolio system instance"""
    return trading_system


def start_trading_system() -> None:
    """Start the multi-asset portfolio system using native .run() methods"""
    trading_system.start_background_trading()


def stop_trading_system() -> None:
    """Stop the multi-asset portfolio system"""
    trading_system.stop_background_trading()

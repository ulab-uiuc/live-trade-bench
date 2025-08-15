"""
Multi-Asset Trading System Integration using existing .run() methods from trading_bench

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

import pytz

# Add trading_bench to path before any runtime imports
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
    both TradingSystem (stock_agent.py) and PolymarketTradingSystem (polymarket_agent.py)
    """

    def __init__(self):
        # Import the native trading systems using factory functions
        from trading_bench import (
            create_polymarket_trading_system,
            create_stock_trading_system,
        )

        # Create the native trading systems using factory functions
        self.stock_system = create_stock_trading_system()
        self.polymarket_system = create_polymarket_trading_system()

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
                "id": "claude-3.5-sonnet",
                "name": "Claude 3.5 Sonnet",
                "llm_model": "claude-3-5-sonnet-20241022",
            },
            {"id": "gpt-5", "name": "GPT-5", "llm_model": "gpt-5"},
            {"id": "gpt-4o", "name": "GPT-4o", "llm_model": "gpt-4o"},
            {
                "id": "gemini-2.5-pro",
                "name": "Gemini 2.5 Pro",
                "llm_model": "gemini-2.5-pro",
            },
            {
                "id": "claude-4-sonnet",
                "name": "Claude 4 Sonnet",
                "llm_model": "claude-sonnet-4-20250514",
            },
            {"id": "grok-4", "name": "Grok 4", "llm_model": "grok-4-0709"},
            {
                "id": "deepseek-chat",
                "name": "Deepseek V3 (Chat)",
                "llm_model": "deepseek-chat",
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
            "Multi-asset trading system initialized using native .run() methods"
        )

    def _initialize_models(self):
        """Initialize agents in both native trading systems"""

        # Initialize stock agents using native TradingSystem.add_agent()
        for model_config in self.models_config:
            model_id = model_config["id"]
            model_name = model_config["name"]
            llm_model = model_config["llm_model"]

            # Add agent to stock system using native method
            self.stock_system.add_agent(
                name=f"{model_name} (Stock)",
                initial_cash=self.stock_initial_cash,
                model_name=llm_model,
            )

            # Add agent to polymarket system using native method
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

    def _update_news_cache(self):
        """Update the news cache in background"""
        try:
            # Import here to avoid circular imports
            from trading_bench.fetchers.news_fetcher import NewsFetcher

            logger.info("Updating background news cache")

            # Calculate date range (last 7 days)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)

            # Use NewsFetcher directly with correct method and parameters
            news_fetcher = NewsFetcher()
            news_articles = news_fetcher.fetch(
                query="stock market",
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
                max_pages=3,  # Limit to first 3 pages for faster fetching
            )

            # Transform to dict format for JSON serialization
            self.cached_news = []
            for i, article in enumerate(news_articles):
                # Parse the date string to ISO format
                try:
                    published_at = (
                        datetime.now().isoformat()
                    )  # Default to now if parsing fails
                    if article.get("date"):
                        # Try to parse the date (Google News date format can vary)
                        # For now, use current time - in production you'd parse the actual date
                        published_at = datetime.now().isoformat()
                except Exception:
                    published_at = datetime.now().isoformat()

                self.cached_news.append(
                    {
                        "id": f"news_{i}_{int(datetime.now().timestamp())}",
                        "title": article.get("title", "No title"),
                        "summary": article.get("snippet", "No summary"),
                        "source": article.get("source", "Unknown"),
                        "published_at": published_at,
                        "impact": "medium",  # Default impact
                        "category": "market",  # Default category
                        "url": article.get("link", ""),
                    }
                )

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

    def _update_social_cache(self):
        """Update the social media cache in background"""
        try:
            # Import here to avoid circular imports
            from trading_bench.fetchers.reddit_fetcher import RedditFetcher

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
                stock_agent = self.stock_system.agents[agent_name]
                stock_account = self.stock_system.accounts[agent_name]

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
                polymarket_agent = self.polymarket_system.agents[agent_name]
                polymarket_account = self.polymarket_system.accounts[agent_name]

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

    def _calculate_stock_accuracy(self, account) -> float:
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

    def _calculate_polymarket_accuracy(self, account) -> float:
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
        self, model_id: str = None, hours: int = 24
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
                return self.stock_system.universe
            else:
                # Fallback: fetch trending stocks directly
                from trading_bench import fetch_trending_stocks

                trending_stocks = fetch_trending_stocks(limit=10)
                return [s["ticker"] for s in trending_stocks]
        except Exception as e:
            logger.warning(f"Could not get stock tickers: {e}")
            # Ultimate fallback to ensure API doesn't break
            return ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA"]

    def activate_model(self, model_id: str, category: str = None) -> bool:
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

    def deactivate_model(self, model_id: str, category: str = None) -> bool:
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

    def run_trading_cycle(self):
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

    def _run_stock_cycle_native(self):
        """Run stock cycle using native StockTradingSystem.run() - adapted for backend service"""
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

    def _run_polymarket_cycle_native(self):
        """Run polymarket cycle using native PolymarketTradingSystem.run() - matching polymarket_demo.py"""
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
                    agent = self.stock_system.agents[agent_name]
                    account = self.stock_system.accounts[agent_name]
                evaluation = account.evaluate()

                # Extract holdings and detailed position info for frontend compatibility
                holdings = {}
                positions = {}

                # Get active positions from account
                try:
                    active_positions = account.get_active_positions()
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
                    "model_name": agent.name,
                    "category": "stock",
                    "cash": account.cash_balance,
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
                    agent = self.polymarket_system.agents[agent_name]
                    account = self.polymarket_system.accounts[agent_name]
                evaluation = account.evaluate()

                # Extract holdings and detailed position info for polymarket
                holdings = {}
                positions = {}

                # Get active positions from polymarket account
                try:
                    active_positions = account.get_active_positions()
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
                    "model_name": agent.name,
                    "category": "polymarket",
                    "cash": account.cash_balance,
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

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get comprehensive system performance metrics"""
        total_stock_value = 0.0
        total_polymarket_value = 0.0
        total_initial_stock = len(self.stock_system.agents) * self.stock_initial_cash
        total_initial_polymarket = (
            len(self.polymarket_system.agents) * self.polymarket_initial_cash
        )

        # Calculate total system performance from native systems
        for agent_name in self.stock_system.agents.keys():
            try:
                account = self.stock_system.accounts[agent_name]
                evaluation = account.evaluate()
                total_stock_value += evaluation["portfolio_summary"]["total_value"]
            except Exception:
                total_stock_value += self.stock_initial_cash

        for agent_name in self.polymarket_system.agents.keys():
            try:
                account = self.polymarket_system.accounts[agent_name]
                evaluation = account.evaluate()
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
            "native_systems": {
                "stock_agents": len(self.stock_system.agents),
                "polymarket_agents": len(self.polymarket_system.agents),
                "using_native_run": True,
            },
        }

    def _add_execution_log(self, event_type: str, data: Dict[str, Any]):
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
        self, limit: int = 100, event_type: str = None
    ) -> List[Dict[str, Any]]:
        """Get recent execution logs"""
        logs = self.execution_logs

        if event_type:
            logs = [log for log in logs if log["event_type"] == event_type]

        return sorted(logs, key=lambda x: x["timestamp"], reverse=True)[:limit]

    def start_background_trading(self):
        """Start background trading thread using native .run() methods"""
        if self.system_running:
            logger.warning("Multi-asset trading system already running")
            return

        self.system_running = True
        self.trading_thread = threading.Thread(
            target=self._background_trading_loop, daemon=True
        )
        self.trading_thread.start()
        logger.info(
            "Multi-asset background trading started using native .run() methods"
        )

    def stop_background_trading(self):
        """Stop background trading"""
        self.system_running = False
        if self.trading_thread:
            self.trading_thread.join(timeout=5)
        logger.info("Multi-asset background trading stopped")

    def _background_trading_loop(self):
        """Background trading loop using native .run() methods"""
        logger.info(
            f"Multi-asset trading loop started using native .run() methods with {self.cycle_interval//60} minute intervals"
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
                            f"Multi-asset trading system running using native .run() - next cycle in {remaining_minutes} minutes"
                        )

            except Exception as e:
                logger.error(f"Error in multi-asset trading loop: {e}")
                time.sleep(60)

        logger.info("Multi-asset trading loop stopped")


# Global multi-asset trading system instance
trading_system = MultiAssetTradingSystem()


def get_trading_system() -> MultiAssetTradingSystem:
    """Get the global multi-asset trading system instance"""
    return trading_system


def start_trading_system():
    """Start the multi-asset trading system using native .run() methods"""
    trading_system.start_background_trading()


def stop_trading_system():
    """Stop the multi-asset trading system"""
    trading_system.stop_background_trading()

"""
Core Trading System Integration with trading_bench

This module creates persistent AI trading agents that compete against each other
using real market data and LLM-powered decision making.
"""

import logging
import os
import sys
import threading
import time
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Dict, List, Optional

# Add trading_bench to path before any runtime imports (keep imports at top for linting)
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, project_root)

# Type-only imports to avoid E402 while keeping annotations
if TYPE_CHECKING:  # pragma: no cover - type checking only
    from trading_bench.accounts import StockAccount  # noqa: F401
    from trading_bench.agents.agent import AITradingAgent  # noqa: F401

logger = logging.getLogger(__name__)


class LiveTradingSystem:
    """
    Persistent trading system that runs AI agents continuously
    Each LLM model gets its own agent and account for fair competition
    """

    def __init__(self):
        # Runtime imports (after sys.path adjustments) to avoid E402

        self.agents: Dict[str, "AITradingAgent"] = {}
        self.accounts: Dict[str, "StockAccount"] = {}
        self.trading_history: List[Dict[str, Any]] = []
        self.system_running = False
        self.trading_thread: Optional[threading.Thread] = None

        # Trading configuration
        self.tickers = ["AAPL", "NVDA", "TSLA", "MSFT", "GOOGL", "AMZN", "META"]
        self.cycle_interval = 30 * 60  # 30 minutes between cycles
        self.initial_cash = 1000.0

        # Model activation controls
        self.active_models: Dict[str, bool] = {}

        # Performance tracking
        self.cycle_count = 0
        self.last_cycle_time: Optional[datetime] = None
        self.next_cycle_time: Optional[datetime] = None
        self.execution_stats = {
            "total_cycles": 0,
            "successful_cycles": 0,
            "failed_cycles": 0,
            "total_actions": 0,
            "successful_actions": 0,
            "failed_actions": 0,
        }

        # Detailed execution logs
        self.execution_logs: List[Dict[str, Any]] = []
        self.max_log_entries = 1000  # Keep last 1000 log entries

        # System startup time
        self.start_time = datetime.now()

        # Initialize models
        self._initialize_models()

        logger.info(f"Trading system initialized with {len(self.agents)} agents")

    def _initialize_models(self):
        """Initialize AI agents for each LLM model"""
        # Import factory after path setup
        from trading_bench.accounts import create_stock_account  # type: ignore
        from trading_bench.agents.agent import AITradingAgent  # type: ignore

        models_config = [
            {
                "id": "claude-3.5-sonnet",
                "name": "Claude 3.5 Sonnet",
                "llm_model": "claude-3-5-sonnet-20241022",
            },
            {"id": "gpt-4", "name": "GPT-4", "llm_model": "gpt-4"},
            {
                "id": "gemini-1.5-pro",
                "name": "Gemini 1.5 Pro",
                "llm_model": "gemini-1.5-pro",
            },
            {
                "id": "claude-4-haiku",
                "name": "Claude 4 Haiku",
                "llm_model": "claude-3-haiku-20240307",
            },
        ]

        for model_config in models_config:
            model_id = model_config["id"]
            model_name = model_config["name"]
            llm_model = model_config["llm_model"]

            # Create AI agent
            agent = AITradingAgent(name=model_name, model_name=llm_model)

            # Create dedicated account
            account = create_stock_account(
                initial_cash=self.initial_cash, commission_rate=0.001  # 0.1% commission
            )

            self.agents[model_id] = agent
            self.accounts[model_id] = account
            self.active_models[model_id] = True  # All models start active

            logger.info(
                f"Initialized {model_name} with ${self.initial_cash} starting capital"
            )

    def get_model_data(self) -> List[Dict[str, Any]]:
        """Get current model performance data"""
        models_data = []

        for model_id, agent in self.agents.items():
            account = self.accounts[model_id]

            try:
                # Get account evaluation
                evaluation = account.evaluate()
                portfolio_summary = evaluation["portfolio_summary"]

                # Calculate performance metrics
                total_value = portfolio_summary["total_value"]
                return_pct = portfolio_summary["return_pct"]
                trades_count = len(account.transactions)
                profit = portfolio_summary["total_return"]

                # Determine status based on activation and recent activity
                is_activated = self.active_models.get(model_id, True)
                recent_actions = self.get_recent_actions(model_id, hours=2)

                if not is_activated:
                    status = "inactive"
                elif recent_actions:
                    status = "active"
                else:
                    status = "inactive"

                # Calculate accuracy (simplified - profitable trades / total trades)
                profitable_trades = len(
                    [
                        t
                        for t in account.transactions
                        if t.action == "sell" and self._is_profitable_sell(account, t)
                    ]
                )
                accuracy = (profitable_trades / max(trades_count, 1)) * 100

                # Enhanced performance metrics
                daily_actions = self.get_recent_actions(model_id, hours=24)
                weekly_actions = self.get_recent_actions(model_id, hours=168)

                # Calculate win rate from recent actions
                recent_successful = len(
                    [a for a in daily_actions if a.get("status") == "executed"]
                )
                recent_total = len(daily_actions)
                recent_win_rate = (recent_successful / max(recent_total, 1)) * 100

                # Trading frequency
                actions_per_day = len(daily_actions)
                actions_per_week = len(weekly_actions)

                model_data = {
                    "id": model_id,
                    "name": agent.name,
                    "performance": return_pct,
                    "accuracy": accuracy,
                    "trades": trades_count,
                    "profit": profit,
                    "status": status,
                    "total_value": total_value,
                    "cash_balance": account.cash_balance,
                    "active_positions": len(account.get_active_positions()),
                    "is_activated": self.active_models.get(model_id, True),
                    "recent_performance": {
                        "daily_actions": actions_per_day,
                        "weekly_actions": actions_per_week,
                        "recent_win_rate": recent_win_rate,
                        "last_action_time": daily_actions[0]["timestamp"]
                        if daily_actions
                        else None,
                    },
                    "llm_available": agent.available,
                }

                models_data.append(model_data)

            except Exception as e:
                logger.error(f"Error getting data for {model_id}: {e}")
                # Return default data if error
                models_data.append(
                    {
                        "id": model_id,
                        "name": agent.name,
                        "performance": 0.0,
                        "accuracy": 0.0,
                        "trades": 0,
                        "profit": 0.0,
                        "status": "inactive",
                        "total_value": self.initial_cash,
                        "cash_balance": self.initial_cash,
                        "active_positions": 0,
                    }
                )

        return models_data

    def _is_profitable_sell(self, account: "StockAccount", transaction) -> bool:
        """Check if a sell transaction was profitable (simplified)"""
        try:
            # Find the corresponding buy transactions for this ticker
            buy_transactions = [
                t
                for t in account.transactions
                if t.ticker == transaction.ticker
                and t.action == "buy"
                and t.timestamp < transaction.timestamp
            ]

            if buy_transactions:
                # Use average buy price for simplification
                avg_buy_price = sum(t.price for t in buy_transactions) / len(
                    buy_transactions
                )
                return transaction.price > avg_buy_price

        except Exception:
            pass
        return False

    def get_recent_actions(
        self, model_id: str = None, hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Get recent trading actions"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        actions = []
        for action in self.trading_history:
            action_time = datetime.fromisoformat(action["timestamp"])
            if action_time >= cutoff_time:
                if model_id is None or action["agent_id"] == model_id:
                    actions.append(action)

        return sorted(actions, key=lambda x: x["timestamp"], reverse=True)

    def get_portfolio(self, model_id: str) -> Dict[str, Any]:
        """Get portfolio data for a specific model with real-time P&L"""
        if model_id not in self.accounts:
            raise ValueError(f"Model {model_id} not found")

        account = self.accounts[model_id]
        evaluation = account.evaluate()

        # Get current market prices for real-time P&L
        current_prices = self._get_current_prices()
        positions_data = evaluation["portfolio_assets"]

        # Calculate real-time unrealized P&L
        total_unrealized_pnl = 0.0
        total_market_value = 0.0

        for ticker, position in positions_data.items():
            if ticker in current_prices:
                current_price = current_prices[ticker]
                quantity = position["quantity"]
                current_value = quantity * current_price
                cost_basis = position["cost_basis"]
                unrealized_pnl = current_value - cost_basis

                # Update position with real-time data
                position["current_price_realtime"] = current_price
                position["current_value_realtime"] = current_value
                position["unrealized_pnl_realtime"] = unrealized_pnl
                position["unrealized_pnl_pct_realtime"] = (
                    (unrealized_pnl / cost_basis * 100) if cost_basis > 0 else 0.0
                )

                total_unrealized_pnl += unrealized_pnl
                total_market_value += current_value

        # Calculate total portfolio value with real-time prices
        total_value_realtime = account.cash_balance + total_market_value
        total_return_realtime = total_value_realtime - self.initial_cash
        return_pct_realtime = (
            (total_return_realtime / self.initial_cash * 100)
            if self.initial_cash > 0
            else 0.0
        )

        return {
            "model_id": model_id,
            "model_name": self.agents[model_id].name,
            "cash": account.cash_balance,
            "holdings": {
                ticker: position["quantity"]
                for ticker, position in positions_data.items()
            },
            "total_value": evaluation["portfolio_summary"]["total_value"],
            "total_value_realtime": total_value_realtime,
            "return_pct": evaluation["portfolio_summary"]["return_pct"],
            "return_pct_realtime": return_pct_realtime,
            "unrealized_pnl": evaluation["portfolio_summary"]["unrealized_pnl"],
            "unrealized_pnl_realtime": total_unrealized_pnl,
            "positions": positions_data,
            "market_data_available": len(current_prices) > 0,
            "last_updated": datetime.now().isoformat(),
        }

    def activate_model(self, model_id: str) -> bool:
        """Activate a trading model"""
        if model_id in self.agents:
            self.active_models[model_id] = True
            logger.info(f"Activated model: {model_id}")
            return True
        return False

    def deactivate_model(self, model_id: str) -> bool:
        """Deactivate a trading model"""
        if model_id in self.agents:
            self.active_models[model_id] = False
            logger.info(f"Deactivated model: {model_id}")
            return True
        return False

    def set_cycle_interval(self, minutes: int) -> bool:
        """Set trading cycle interval in minutes"""
        if minutes >= 1:
            self.cycle_interval = minutes * 60
            logger.info(f"Set cycle interval to {minutes} minutes")
            return True
        return False

    def run_trading_cycle(self):
        """Run one trading cycle for all active agents"""
        cycle_start_time = datetime.now()
        self.execution_stats["total_cycles"] += 1

        try:
            logger.info(
                f"Starting trading cycle #{self.execution_stats['total_cycles']}"
            )

            # Get current prices for all tickers
            current_prices = self._get_current_prices()

            if not current_prices:
                logger.warning("No prices available, skipping cycle")
                self.execution_stats["failed_cycles"] += 1
                return

            cycle_actions = []

            # Only run active agents
            active_agent_count = 0
            for model_id, agent in self.agents.items():
                if not self.active_models.get(model_id, True):
                    logger.debug(f"Skipping deactivated model: {agent.name}")
                    continue

                active_agent_count += 1
                account = self.accounts[model_id]

                logger.info(f"Running cycle for {agent.name}")

                for ticker in self.tickers:
                    if ticker not in current_prices:
                        continue

                    current_price = current_prices[ticker]

                    try:
                        # Agent generates action
                        stock_action = agent.generate_action(
                            ticker, current_price, account
                        )

                        if stock_action:
                            # Execute action
                            success, message, transaction = account.execute_action(
                                stock_action
                            )

                            # Update execution stats
                            self.execution_stats["total_actions"] += 1
                            if success:
                                self.execution_stats["successful_actions"] += 1
                            else:
                                self.execution_stats["failed_actions"] += 1

                            # Log action
                            action_log = {
                                "id": f"{model_id}_{ticker}_{int(datetime.now().timestamp())}",
                                "agent_id": model_id,
                                "agent_name": agent.name,
                                "agent_type": "trading_agent",
                                "action": stock_action.action.upper(),
                                "description": f"{stock_action.action.upper()} {stock_action.quantity} {ticker} @ ${stock_action.price:.2f}",
                                "status": "executed" if success else "failed",
                                "timestamp": datetime.now().isoformat(),
                                "targets": [ticker],
                                "metadata": {
                                    "ticker": ticker,
                                    "price": stock_action.price,
                                    "quantity": stock_action.quantity,
                                    "message": message,
                                    "success": success,
                                    "cycle": self.execution_stats["total_cycles"],
                                },
                            }

                            self.trading_history.append(action_log)
                            cycle_actions.append(action_log)

                            logger.info(f"{agent.name}: {message}")
                        else:
                            # No action taken - agent requires real LLM to make decisions
                            if not agent.available:
                                logger.debug(
                                    f"{agent.name}: No action for {ticker} - LLM not available"
                                )

                    except Exception as e:
                        logger.error(f"Error in {agent.name} for {ticker}: {e}")
                        self.execution_stats["failed_actions"] += 1

            # Update cycle tracking
            self.last_cycle_time = cycle_start_time
            self.next_cycle_time = cycle_start_time + timedelta(
                seconds=self.cycle_interval
            )
            self.execution_stats["successful_cycles"] += 1

            cycle_duration = (datetime.now() - cycle_start_time).total_seconds()
            logger.info(
                f"Cycle completed: {active_agent_count} active agents, {len(cycle_actions)} actions, {cycle_duration:.1f}s"
            )

            # Log cycle execution
            self._add_execution_log(
                "cycle_completed",
                {
                    "cycle_number": self.execution_stats["total_cycles"],
                    "duration_seconds": cycle_duration,
                    "active_agents": active_agent_count,
                    "actions_taken": len(cycle_actions),
                    "prices_available": len(current_prices),
                    "tickers": list(current_prices.keys()),
                },
            )

        except Exception as e:
            logger.error(f"Error in trading cycle: {e}")
            self.execution_stats["failed_cycles"] += 1

            # Log cycle failure
            self._add_execution_log(
                "cycle_failed",
                {
                    "cycle_number": self.execution_stats["total_cycles"],
                    "error": str(e),
                    "duration_seconds": (
                        datetime.now() - cycle_start_time
                    ).total_seconds(),
                },
            )

    def _get_current_prices(self) -> Dict[str, float]:
        """Get current prices for all tickers - returns empty dict if data unavailable"""
        try:
            from trading_bench.fetchers.stock_fetcher import get_current_stock_price

            prices = {}
            for ticker in self.tickers:
                try:
                    price = get_current_stock_price(ticker)
                    if price and price > 0:
                        prices[ticker] = price
                except Exception as e:
                    logger.warning(f"Failed to get price for {ticker}: {e}")

            if not prices:
                logger.warning("No real prices available - skipping trading cycle")

            return prices

        except Exception as e:
            logger.error(f"Error fetching prices: {e}")
            return {}

    def _add_execution_log(self, event_type: str, data: Dict[str, Any]):
        """Add entry to execution logs"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
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

        # Filter by event type if specified
        if event_type:
            logs = [log for log in logs if log["event_type"] == event_type]

        # Return most recent entries
        return sorted(logs, key=lambda x: x["timestamp"], reverse=True)[:limit]

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get comprehensive system performance metrics"""
        total_portfolio_value = 0.0
        total_initial_value = len(self.agents) * self.initial_cash

        # Calculate total system performance
        for model_id in self.agents.keys():
            try:
                account = self.accounts[model_id]
                evaluation = account.evaluate()
                total_portfolio_value += evaluation["portfolio_summary"]["total_value"]
            except Exception as e:
                logger.warning(
                    f"Failed to evaluate account {model_id}: {e}; using initial_cash fallback"
                )
                total_portfolio_value += self.initial_cash  # Fallback to initial value

        system_return_pct = (
            ((total_portfolio_value - total_initial_value) / total_initial_value * 100)
            if total_initial_value > 0
            else 0.0
        )

        # Calculate uptime
        if hasattr(self, "start_time"):
            uptime_seconds = (datetime.now() - self.start_time).total_seconds()
        else:
            uptime_seconds = 0

        return {
            "system_performance": {
                "total_portfolio_value": total_portfolio_value,
                "total_initial_value": total_initial_value,
                "system_return_pct": system_return_pct,
                "uptime_seconds": uptime_seconds,
                "uptime_hours": uptime_seconds / 3600,
            },
            "execution_stats": self.execution_stats,
            "active_models_count": len(
                [m for m, active in self.active_models.items() if active]
            ),
            "total_models_count": len(self.agents),
            "recent_logs_count": len(self.execution_logs),
            "avg_cycle_duration": self._calculate_avg_cycle_duration(),
            "success_rate": {
                "cycles": (
                    self.execution_stats["successful_cycles"]
                    / max(self.execution_stats["total_cycles"], 1)
                )
                * 100,
                "actions": (
                    self.execution_stats["successful_actions"]
                    / max(self.execution_stats["total_actions"], 1)
                )
                * 100,
            },
        }

    def _calculate_avg_cycle_duration(self) -> float:
        """Calculate average cycle duration from logs"""
        cycle_logs = [
            log for log in self.execution_logs if log["event_type"] == "cycle_completed"
        ]
        if not cycle_logs:
            return 0.0

        durations = [
            log["data"].get("duration_seconds", 0) for log in cycle_logs[-10:]
        ]  # Last 10 cycles
        return sum(durations) / len(durations) if durations else 0.0

    def start_background_trading(self):
        """Start background trading thread"""
        if self.system_running:
            logger.warning("Trading system already running")
            return

        self.system_running = True
        self.trading_thread = threading.Thread(
            target=self._background_trading_loop, daemon=True
        )
        self.trading_thread.start()
        logger.info("Background trading started")

    def stop_background_trading(self):
        """Stop background trading"""
        self.system_running = False
        if self.trading_thread:
            self.trading_thread.join(timeout=5)
        logger.info("Background trading stopped")

    def _background_trading_loop(self):
        """Background trading loop with enhanced monitoring"""
        logger.info(
            f"Trading loop started with {self.cycle_interval//60} minute intervals"
        )

        while self.system_running:
            try:
                # Check if any models are active
                active_models = [
                    model_id
                    for model_id, active in self.active_models.items()
                    if active
                ]

                if not active_models:
                    logger.info("No active models - skipping trading cycle")
                else:
                    logger.info(
                        f"Running cycle with {len(active_models)} active models: {active_models}"
                    )
                    self.run_trading_cycle()

                # Update next cycle time
                self.next_cycle_time = datetime.now() + timedelta(
                    seconds=self.cycle_interval
                )

                # Wait for next cycle with periodic status updates
                wait_time = 0
                status_interval = 300  # 5 minutes

                while wait_time < self.cycle_interval and self.system_running:
                    time.sleep(
                        min(60, self.cycle_interval - wait_time)
                    )  # Sleep in 1-minute chunks
                    wait_time += 60

                    # Log status every 5 minutes
                    if wait_time % status_interval == 0 and self.system_running:
                        remaining_minutes = (self.cycle_interval - wait_time) // 60
                        logger.info(
                            f"Trading system running - next cycle in {remaining_minutes} minutes"
                        )

            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                time.sleep(60)  # Wait before retrying

        logger.info("Trading loop stopped")


# Global trading system instance
trading_system = LiveTradingSystem()


def get_trading_system() -> LiveTradingSystem:
    """Get the global trading system instance"""
    return trading_system


def start_trading_system():
    """Start the trading system (called on app startup)"""
    trading_system.start_background_trading()


def stop_trading_system():
    """Stop the trading system (called on app shutdown)"""
    trading_system.stop_background_trading()

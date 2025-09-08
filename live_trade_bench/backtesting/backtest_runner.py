"""
Backtest Runner - Simple time controller for both stock and polymarket

Linus principle: "Good code has no special cases"
Just controls time flow, uses existing systems unchanged.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple

from ..agents.polymarket_system import PolymarketPortfolioSystem
from ..agents.stock_system import StockPortfolioSystem


class BacktestRunner:
    """
    Time controller for backtesting. Nothing fancy.

    Existing systems do all the work, we just control what "today" means.
    """

    def __init__(
        self, start_date: str, end_date: str, market_type: str = "stock"
    ) -> None:
        """
        Args:
            start_date: YYYY-MM-DD
            end_date: YYYY-MM-DD
            market_type: "stock" or "polymarket"
        """
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.end_date = datetime.strptime(end_date, "%Y-%m-%d")
        self.market_type = market_type

        # Use existing systems - zero special cases
        if market_type == "stock":
            self.system = StockPortfolioSystem()
        else:
            self.system = PolymarketPortfolioSystem()

        self.agents: List[Dict[str, Any]] = []

    def add_agent(
        self, name: str, initial_cash: float = 1000.0, model_name: str = "gpt-4o-mini"
    ) -> None:
        """Add agent to backtest."""
        self.agents.append(
            {"name": name, "initial_cash": initial_cash, "model_name": model_name}
        )

    def run(self) -> Dict[str, Any]:
        """
        Run backtest.

        Process all agents within a single portfolio system.
        """
        print(
            f"🚀 Starting {self.market_type} backtest: {self.start_date.strftime('%Y-%m-%d')} → {self.end_date.strftime('%Y-%m-%d')}"
        )
        print(f"🤖 Processing {len(self.agents)} agents in single system")

        # Add all agents to the initialized system
        for agent in self.agents:
            self.system.add_agent(
                agent["name"], agent["initial_cash"], agent["model_name"]
            )

        # Simulate trading period - loop over trading days
        trading_days = self._get_trading_days()

        # Run cycles equal to number of trading days
        try:
            print(f"📅 Running backtest for {len(trading_days)} days...")
            for day_index, current_day in enumerate(trading_days, start=1):
                print(
                    f"\n===== 📆 Day {day_index}/{len(trading_days)}: {current_day.strftime('%Y-%m-%d')} ====="
                )
                # Pass date only for stock system which supports date-specific pricing
                if self.market_type == "stock":
                    self.system.run_cycle(current_day.strftime("%Y-%m-%d"))
                else:
                    self.system.run_cycle()

            # Extract results for each agent
            final_results = {}
            for agent in self.agents:
                agent_name = agent["name"]
                initial_cash = agent["initial_cash"]

                # Get final portfolio value from the agent's account
                if agent_name in self.system.agents:
                    agent_account = self.system.agents[agent_name].account
                    final_value = agent_account.get_total_value()
                    return_pct = ((final_value - initial_cash) / initial_cash) * 100

                    final_results[agent_name] = {
                        "initial_value": initial_cash,
                        "final_value": final_value,
                        "return_percentage": return_pct,
                        "period": f"{self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}",
                    }
                else:
                    # Fallback if agent not found
                    final_results[agent_name] = {
                        "initial_value": initial_cash,
                        "final_value": initial_cash,
                        "return_percentage": 0.0,
                        "period": f"{self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}",
                    }

            return final_results

        except Exception as e:
            print(f"❌ Backtest error: {e}")
            import traceback

            traceback.print_exc()

            # Return error results for all agents
            error_results = {}
            for agent in self.agents:
                error_results[agent["name"]] = {
                    "initial_value": agent["initial_cash"],
                    "final_value": agent["initial_cash"],
                    "return_percentage": 0.0,
                    "period": f"{self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}",
                    "error": str(e),
                }
            return error_results

    def _get_trading_days(self) -> List[datetime]:
        """Get trading days in backtest period (weekdays only)."""
        days: List[datetime] = []
        current = self.start_date

        while current <= self.end_date:
            # Only include weekdays (Mon-Fri). Systems can still handle closures.
            if current.weekday() < 5:
                days.append(current)
            current += timedelta(days=1)

        return days


# Simple wrapper function for backtesting (merged from backtest_system)
def run_backtest(
    models: List[Tuple[str, str]],  # [(name, model_id), ...]
    initial_cash: float,
    start_date: str,
    end_date: str,
    market_type: str = "stock",
) -> Dict[str, Any]:
    """
    Run backtest with multiple models - simplified interface.

    Args:
        models: List of (name, model_id) tuples, e.g. [("GPT-4o", "gpt-4o")]
        initial_cash: Initial cash for each model
        start_date: YYYY-MM-DD
        end_date: YYYY-MM-DD
        market_type: "stock" or "polymarket"

    Returns:
        Backtest results with all models processed concurrently
    """
    runner = BacktestRunner(start_date, end_date, market_type=market_type)

    for name, model_id in models:
        runner.add_agent(name=name, initial_cash=initial_cash, model_name=model_id)

    return runner.run()

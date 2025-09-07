"""
Backtest Runner - Simple time controller for both stock and polymarket

Linus principle: "Good code has no special cases"
Just controls time flow, uses existing systems unchanged.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List

from ..agents.polymarket_system import PolymarketPortfolioSystem
from ..agents.stock_system import StockPortfolioSystem
from ..fetchers.polymarket_fetcher import PolymarketFetcher
from ..fetchers.stock_fetcher import StockFetcher


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
            self.fetcher = StockFetcher()
        else:
            self.system = PolymarketPortfolioSystem()
            self.fetcher = PolymarketFetcher()

        self.agents: List[Dict[str, Any]] = []

    def add_agent(
        self, name: str, initial_cash: float = 1000.0, model_name: str = "gpt-4o-mini"
    ) -> None:
        """Add agent to backtest."""
        self.agents.append(
            {"name": name, "initial_cash": initial_cash, "model_name": model_name}
        )

    async def run(self) -> Dict[str, Any]:
        """
        Run backtest with async concurrency.

        Process all agents concurrently within a single portfolio system.
        """
        print(
            f"🚀 Starting {self.market_type} backtest: {self.start_date.strftime('%Y-%m-%d')} → {self.end_date.strftime('%Y-%m-%d')}"
        )
        print(f"🤖 Processing {len(self.agents)} agents concurrently in single system")

        # Create ONE system for ALL agents - major architecture fix!
        if self.market_type == "stock":
            from ..agents.stock_system import StockPortfolioSystem

            portfolio_system = StockPortfolioSystem()
        else:
            from ..agents.polymarket_system import PolymarketPortfolioSystem

            portfolio_system = PolymarketPortfolioSystem()

        # Add all agents to the SAME system
        for agent in self.agents:
            portfolio_system.add_agent(
                agent["name"], agent["initial_cash"], agent["model_name"]
            )

        # Simulate trading period - ONE system call for ALL agents
        trading_days = self._get_trading_days()

        # Run one cycle with all agents concurrently
        try:
            print(f"📅 Running backtest cycle for {len(trading_days)} days...")
            await portfolio_system.run_cycle()

            # Extract results for each agent
            final_results = {}
            for agent in self.agents:
                agent_name = agent["name"]
                initial_cash = agent["initial_cash"]

                # Get final portfolio value from the agent's account
                if agent_name in portfolio_system.agents:
                    agent_account = portfolio_system.agents[agent_name].account
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
        """Get trading days in backtest period."""
        days = []
        current = self.start_date

        while current <= self.end_date:
            # For simplicity, include all days (systems handle market closures)
            days.append(current)
            current += timedelta(days=1)

        return days

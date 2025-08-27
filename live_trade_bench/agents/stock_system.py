from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Dict, List

from ..accounts import StockAccount, create_stock_account
from ..fetchers.stock_fetcher import fetch_current_stock_price, fetch_trending_stocks
from .stock_agent import LLMStockAgent


class StockPortfolioSystem:
    """Stock portfolio management system using AI agents."""

    def __init__(self, universe_size: int = 10) -> None:
        self.agents: Dict[str, LLMStockAgent] = {}
        self.accounts: Dict[str, StockAccount] = {}
        self.universe: List[Dict[str, Any]] = []
        self._init_universe(universe_size)

    def _init_universe(self, limit: int) -> None:
        """Initialize stock universe."""
        stocks = fetch_trending_stocks(limit=limit)
        self.universe = [
            {
                "ticker": s["ticker"],
                "name": s.get("name", s["ticker"]),
                "sector": s.get("sector", "Unknown"),
                "market_cap": s.get("market_cap", 0),
            }
            for s in stocks
        ]

    def add_agent(
        self, name: str, initial_cash: float = 10000.0, model_name: str = "gpt-4o-mini"
    ) -> None:
        """Add a new portfolio agent."""
        self.agents[name] = LLMStockAgent(name, model_name)
        self.accounts[name] = create_stock_account(initial_cash)

    def _fetch_market_data(self) -> Dict[str, Dict[str, Any]]:
        """Fetch current market data for all stocks."""
        market_data = {}
        for stock in self.universe:
            ticker = stock["ticker"]
            try:
                price_data = fetch_current_stock_price(ticker)
                if price_data and "current_price" in price_data:
                    market_data[ticker] = {
                        "ticker": ticker,
                        "name": stock["name"],
                        "sector": stock["sector"],
                        "current_price": float(price_data["current_price"]),
                        "volume": price_data.get("volume", 0),
                        "market_cap": stock.get("market_cap", 0),
                        "timestamp": datetime.now().isoformat(),
                    }
            except Exception as e:
                print(f"⚠️ Failed to fetch data for {ticker}: {e}")

        return market_data

    def run_cycle(self) -> Dict[str, Any]:
        """Run one portfolio management cycle."""
        print(f"🔄 Running portfolio cycle at {datetime.now().strftime('%H:%M:%S')}")

        market_data = self._fetch_market_data()
        if not market_data:
            return {"status": "no_market_data", "timestamp": datetime.now().isoformat()}

        cycle_results = {
            "timestamp": datetime.now().isoformat(),
            "market_data_count": len(market_data),
            "agents_processed": 0,
            "allocations_updated": 0,
            "rebalancing_required": 0,
            "errors": [],
        }

        # Process each agent
        for agent_name, agent in self.agents.items():
            try:
                account = self.accounts[agent_name]
                cycle_results["agents_processed"] += 1

                # Generate portfolio allocations for each stock
                for ticker, stock_data in market_data.items():
                    try:
                        allocation = agent.generate_portfolio_allocation(
                            stock_data, account
                        )
                        if allocation:
                            # Update target allocation
                            success = account.set_target_allocation(
                                allocation["ticker"], allocation["allocation"]
                            )
                            if success:
                                cycle_results["allocations_updated"] += 1
                                print(
                                    f"✅ {agent_name}: Updated {ticker} allocation to {allocation['allocation']:.1%}"
                                )
                            else:
                                cycle_results["errors"].append(
                                    f"Failed to set allocation for {ticker}"
                                )
                    except Exception as e:
                        error_msg = f"Error processing {ticker} for {agent_name}: {e}"
                        cycle_results["errors"].append(error_msg)
                        print(f"⚠️ {error_msg}")

                # Check if rebalancing is needed
                if account.needs_rebalancing():
                    cycle_results["rebalancing_required"] += 1
                    rebalance_plan = account.rebalance_portfolio()

                    if rebalance_plan.get("status") == "rebalancing_required":
                        print(f"🔄 {agent_name}: Rebalancing required")
                        success = account.execute_rebalancing(rebalance_plan)
                        if success:
                            print(f"✅ {agent_name}: Portfolio rebalanced successfully")
                        else:
                            print(f"❌ {agent_name}: Portfolio rebalancing failed")
                    else:
                        print(f"💤 {agent_name}: No rebalancing needed")

            except Exception as e:
                error_msg = f"Error processing agent {agent_name}: {e}"
                cycle_results["errors"].append(error_msg)
                print(f"⚠️ {error_msg}")

        # Print cycle summary
        print(
            f"📊 Cycle Summary: {cycle_results['agents_processed']} agents, "
            f"{cycle_results['allocations_updated']} allocations updated, "
            f"{cycle_results['rebalancing_required']} rebalancing required"
        )

        return cycle_results

    def get_portfolio_summaries(self) -> Dict[str, Dict[str, Any]]:
        """Get portfolio summaries for all agents."""
        summaries = {}
        for agent_name, account in self.accounts.items():
            summaries[agent_name] = account.get_portfolio_summary()
        return summaries

    def get_agent_status(self, agent_name: str) -> Dict[str, Any]:
        """Get detailed status for a specific agent."""
        if agent_name not in self.agents:
            return {"error": "Agent not found"}

        agent = self.agents[agent_name]
        account = self.accounts[agent_name]

        return {
            "agent_name": agent.name,
            "model_name": agent.model_name,
            "available": agent.available,
            "portfolio": account.get_portfolio_summary(),
            "needs_rebalancing": account.needs_rebalancing(),
            "last_rebalance": account.last_rebalance,
        }

    def run_continuous(
        self, interval_minutes: int = 15, max_cycles: int = None
    ) -> None:
        """Run continuous portfolio management cycles."""
        print(
            f"🚀 Starting continuous portfolio management (interval: {interval_minutes} minutes)"
        )

        cycle_count = 0
        try:
            while max_cycles is None or cycle_count < max_cycles:
                cycle_count += 1
                print(f"\n🔄 Cycle {cycle_count}")

                result = self.run_cycle()
                if result.get("errors"):
                    print(f"⚠️ Cycle {cycle_count} had {len(result['errors'])} errors")

                if max_cycles is None or cycle_count < max_cycles:
                    print(f"⏰ Waiting {interval_minutes} minutes until next cycle...")
                    time.sleep(interval_minutes * 60)

        except KeyboardInterrupt:
            print(f"\n⏹️ Stopped after {cycle_count} cycles")
        except Exception as e:
            print(f"❌ Continuous run failed after {cycle_count} cycles: {e}")

    def run(self, duration_minutes: int = 10, interval: int = 60) -> None:
        """Backward compatibility method for old trading system API."""
        print("⚠️ run() method is deprecated, use run_continuous() instead")
        print(
            f"🔄 Running portfolio management for {duration_minutes} minutes with {interval}s intervals"
        )

        # Convert to new API
        interval_minutes = interval / 60.0
        max_cycles = (
            int(duration_minutes / interval_minutes) if interval_minutes > 0 else 1
        )

        self.run_continuous(interval_minutes=interval_minutes, max_cycles=max_cycles)


# Backward compatibility
StockTradingSystem = StockPortfolioSystem


# Factory functions
def create_stock_portfolio_system() -> StockPortfolioSystem:
    """Create a new stock portfolio management system."""
    return StockPortfolioSystem()


def create_stock_trading_system() -> StockPortfolioSystem:
    """Backward compatibility - creates portfolio system."""
    print(
        "⚠️ create_stock_trading_system is deprecated, use create_stock_portfolio_system instead"
    )
    return create_stock_portfolio_system()

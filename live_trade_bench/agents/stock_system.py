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
        self.universe: List[str] = []  # List of ticker strings
        self.stock_info: Dict[str, Dict[str, Any]] = {}  # Additional stock info
        self.cycle_count = 0
        self._init_universe(universe_size)

    def _init_universe(self, limit: int) -> None:
        """Initialize stock universe."""
        tickers = fetch_trending_stocks(limit=limit)
        self.universe = tickers  # Store just the ticker strings

        # Also create a mapping for additional stock info
        self.stock_info = {}
        for ticker in tickers:
            self.stock_info[ticker] = {
                "name": ticker,
                "sector": "Unknown",
                "market_cap": 0,
            }

    def add_agent(
        self, name: str, initial_cash: float = 10000.0, model_name: str = "gpt-4o-mini"
    ) -> None:
        """Add a new portfolio agent."""
        agent = LLMStockAgent(name, model_name)
        account = create_stock_account(initial_cash)

        # Link agent to account
        agent.account = account

        self.agents[name] = agent
        self.accounts[name] = account

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
        print(f"\n🔄 Running portfolio cycle {self.cycle_count}...")

        try:
            # Fetch market data for all stocks
            market_data = {}
            for ticker in self.universe:
                try:
                    # Get current price
                    price = fetch_current_stock_price(ticker)
                    if price:
                        market_data[ticker] = {
                            "ticker": ticker,
                            "name": self.stock_info[ticker]["name"],
                            "sector": self.stock_info[ticker]["sector"],
                            "current_price": price,
                            "market_cap": self.stock_info[ticker]["market_cap"],
                        }

                        # Update position prices if agent has positions
                        for agent in self.agents.values():
                            if hasattr(agent.account, "update_position_price"):
                                agent.account.update_position_price(ticker, price)

                except Exception as e:
                    print(f"⚠️ Failed to fetch data for {ticker}: {e}")

            if not market_data:
                print("❌ No market data available")
                return {"success": False, "error": "No market data"}

            print(f"📊 Fetched data for {len(market_data)} stocks")

            # Generate portfolio allocations for all agents
            for agent_name, agent in self.agents.items():
                try:
                    print(f"\n🤖 {agent_name} generating portfolio allocation...")

                    # Show current portfolio status
                    current_value = agent.account.get_total_value()
                    cash_balance = agent.account.cash_balance
                    print(f"   💰 Current Portfolio Value: ${current_value:,.2f}")
                    print(f"   💵 Current Cash Balance: ${cash_balance:,.2f}")
                    print(
                        f"   📊 Current Target Allocations: {agent.account.target_allocations}"
                    )

                    # Generate complete portfolio allocation
                    allocation = agent.generate_portfolio_allocation(
                        market_data, agent.account
                    )

                    if allocation:
                        # Update target allocations for all stocks
                        for ticker, target_ratio in allocation.items():
                            if ticker in self.universe:
                                agent.account.set_target_allocation(
                                    ticker, target_ratio
                                )
                                print(f"   📈 {ticker}: {target_ratio:.1%}")

                        # After updating allocations, record a snapshot of the new state
                        agent.account._record_allocation_snapshot()

                        print(f"   ✅ Portfolio allocation updated for {agent_name}")
                    else:
                        print(f"   ⚠️ No allocation generated for {agent_name}")

                except Exception as e:
                    print(f"❌ Error processing {agent_name}: {e}")
                    import traceback

                    traceback.print_exc()

            self.cycle_count += 1
            return {
                "success": True,
                "cycle": self.cycle_count,
                "agents_processed": len(self.agents),
            }

        except Exception as e:
            print(f"❌ Cycle error: {e}")
            import traceback

            traceback.print_exc()
            return {"success": False, "error": str(e)}

    @classmethod
    def get_instance(cls):
        if not hasattr(cls, "_instance"):
            cls._instance = create_stock_portfolio_system()
        return cls._instance

    def get_portfolio_summaries(self) -> Dict[str, Dict[str, Any]]:
        """Get portfolio summaries for all agents."""
        summaries = {}
        total_portfolio_value = 0.0

        for agent_name, agent in self.agents.items():
            account = agent.account
            portfolio_info = account.get_portfolio_value_breakdown()

            summary = {
                "agent_name": agent_name,
                "total_value": portfolio_info["total_value"],
                "cash_value": portfolio_info["cash_value"],
                "positions_value": portfolio_info["positions_value"],
                "cash_allocation": portfolio_info["cash_allocation"],
                "positions_allocation": portfolio_info["positions_allocation"],
                "current_allocations": portfolio_info["current_allocations"],
                "target_allocations": portfolio_info["target_allocations"],
                "needs_rebalancing": account.needs_rebalancing(),
                "last_rebalance": account.last_rebalance,
            }

            summaries[agent_name] = summary
            total_portfolio_value += portfolio_info["total_value"]

        # Add overall portfolio summary
        summaries["OVERALL"] = {
            "agent_name": "OVERALL",
            "total_value": total_portfolio_value,
            "cash_value": sum(
                s["cash_value"]
                for s in summaries.values()
                if s["agent_name"] != "OVERALL"
            ),
            "positions_value": sum(
                s["positions_value"]
                for s in summaries.values()
                if s["agent_name"] != "OVERALL"
            ),
            "cash_allocation": (
                sum(
                    s["cash_allocation"]
                    for s in summaries.values()
                    if s["agent_name"] != "OVERALL"
                )
                / len([s for s in summaries.values() if s["agent_name"] != "OVERALL"])
                if summaries
                else 0.0
            ),
            "positions_allocation": (
                sum(
                    s["positions_allocation"]
                    for s in summaries.values()
                    if s["agent_name"] != "OVERALL"
                )
                / len([s for s in summaries.values() if s["agent_name"] != "OVERALL"])
                if summaries
                else 0.0
            ),
            "current_allocations": {},
            "target_allocations": {},
            "needs_rebalancing": any(
                s["needs_rebalancing"]
                for s in summaries.values()
                if s["agent_name"] != "OVERALL"
            ),
            "last_rebalance": None,
        }

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

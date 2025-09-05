from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Dict, List

import pickle
import os

from ..accounts import PolymarketAccount, create_polymarket_account
from ..fetchers.polymarket_fetcher import (
    fetch_current_market_price,
    fetch_trending_markets,
)
from .polymarket_agent import LLMPolyMarketAgent

STATE_FILE = "polymarket_system_state.pkl"

class PolymarketPortfolioSystem:
    """Polymarket portfolio management system using AI agents."""

    def __init__(self, universe_size: int = 5) -> None:
        self.agents: Dict[str, LLMPolyMarketAgent] = {}
        self.accounts: Dict[str, PolymarketAccount] = {}
        self.universe: List[str] = []  # List of market IDs
        self.market_info: Dict[str, Dict[str, Any]] = {}  # Additional market info
        self.cycle_count = 0
        self._init_universe(universe_size)

    def _init_universe(self, limit: int) -> None:
        """Initialize market universe."""
        markets = fetch_trending_markets(limit=limit)
        self.universe = []  # Store just the market IDs

        for m in markets:
            if m.get("token_ids"):
                market_id = m["id"]
                self.universe.append(market_id)
                self.market_info[market_id] = {
                    "question": m.get("question", str(market_id)),
                    "category": m.get("category", "Unknown"),
                    "token_ids": m.get("token_ids", []),
                }

    def add_agent(
        self, name: str, initial_cash: float = 500.0, model_name: str = "gpt-4o-mini"
    ) -> None:
        """Add a new portfolio agent."""
        agent = LLMPolyMarketAgent(name, model_name)
        account = create_polymarket_account(initial_cash)

        # Link agent to account
        agent.account = account

        self.agents[name] = agent
        self.accounts[name] = account
        self.save_state()

    def _fetch_market_data(self) -> Dict[str, Dict[str, Any]]:
        """Fetch current market data for all markets."""
        market_data = {}
        for market_id in self.universe:
            try:
                price_data = fetch_current_market_price(
                    self.market_info[market_id]["token_ids"]
                )
                if price_data and "yes" in price_data:
                    market_data[market_id] = {
                        "id": market_id,
                        "question": self.market_info[market_id]["question"],
                        "category": self.market_info[market_id]["category"],
                        "price": float(price_data["yes"]),
                        "yes_price": float(price_data["yes"]),
                        "no_price": float(
                            price_data.get("no", 1.0 - float(price_data["yes"]))
                        ),
                        "token_ids": self.market_info[market_id]["token_ids"],
                        "timestamp": datetime.now().isoformat(),
                    }
            except Exception as e:
                print(f"⚠️ Failed to fetch data for {market_id}: {e}")

        return market_data

    def run_cycle(self) -> Dict[str, Any]:
        """Run one portfolio management cycle."""
        print(f"\n🔄 Running portfolio cycle {self.cycle_count}...")

        try:
            # Fetch market data for all markets
            market_data = self._fetch_market_data()

            if not market_data:
                print("❌ No market data available")
                return {"success": False, "error": "No market data"}

            print(f"📊 Fetched data for {len(market_data)} markets")

            # Generate portfolio allocations for each agent
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
                        # Update target allocations for all markets
                        for market_id, target_ratio in allocation.items():
                            if market_id in self.universe:
                                agent.account.set_target_allocation(
                                    market_id, target_ratio
                                )
                                print(f"   📈 {market_id}: {target_ratio:.1%}")

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
            self.save_state()
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

    def save_state(self):
        with open(STATE_FILE, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def get_instance(cls):
        if hasattr(cls, "_instance") and cls._instance:
            return cls._instance
        
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "rb") as f:
                cls._instance = pickle.load(f)
                return cls._instance
        
        cls._instance = create_polymarket_portfolio_system()
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
            "cash_allocation": sum(
                s["cash_allocation"]
                for s in summaries.values()
                if s["agent_name"] != "OVERALL"
            )
            / len([s for s in summaries.values() if s["agent_name"] != "OVERALL"])
            if summaries
            else 0.0,
            "positions_allocation": sum(
                s["positions_allocation"]
                for s in summaries.values()
                if s["agent_name"] != "OVERALL"
            )
            / len([s for s in summaries.values() if s["agent_name"] != "OVERALL"])
            if summaries
            else 0.0,
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
            f"🚀 Starting continuous polymarket portfolio management (interval: {interval_minutes} minutes)"
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


# Backward compatibility
PolymarketTradingSystem = PolymarketPortfolioSystem


# Factory functions
def create_polymarket_portfolio_system() -> PolymarketPortfolioSystem:
    """Create a new polymarket portfolio management system."""
    return PolymarketPortfolioSystem()


def create_polymarket_trading_system() -> PolymarketPortfolioSystem:
    """Backward compatibility - creates portfolio system."""
    print(
        "⚠️ create_polymarket_trading_system is deprecated, use create_polymarket_portfolio_system instead"
    )
    return create_polymarket_portfolio_system()

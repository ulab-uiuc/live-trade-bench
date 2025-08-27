from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Any, Dict, List

from ..accounts import PolymarketAccount, create_polymarket_account
from ..fetchers.polymarket_fetcher import (
    fetch_current_market_price,
    fetch_trending_markets,
)
from .polymarket_agent import LLMPolyMarketAgent


class PolymarketPortfolioSystem:
    """Polymarket portfolio management system using AI agents."""

    def __init__(self, universe_size: int = 5) -> None:
        self.agents: Dict[str, LLMPolyMarketAgent] = {}
        self.accounts: Dict[str, PolymarketAccount] = {}
        self.universe: List[Dict[str, Any]] = []
        self._init_universe(universe_size)

    def _init_universe(self, limit: int) -> None:
        """Initialize market universe."""
        markets = fetch_trending_markets(limit=limit)
        self.universe = [
            {
                "id": m["id"],
                "question": m.get("question", str(m["id"])),
                "category": m.get("category", "Unknown"),
                "token_ids": m.get("token_ids", []),
            }
            for m in markets
            if m.get("token_ids")
        ]

    def add_agent(
        self, name: str, initial_cash: float = 500.0, model_name: str = "gpt-4o-mini"
    ) -> None:
        """Add a new portfolio agent."""
        self.agents[name] = LLMPolyMarketAgent(name, model_name)
        self.accounts[name] = create_polymarket_account(initial_cash)

    def _fetch_market_data(self) -> Dict[str, Dict[str, Any]]:
        """Fetch current market data for all markets."""
        market_data = {}
        for market in self.universe:
            market_id = market["id"]
            try:
                price_data = fetch_current_market_price(market["token_ids"])
                if price_data and "yes" in price_data:
                    market_data[market_id] = {
                        "id": market_id,
                        "question": market["question"],
                        "category": market["category"],
                        "price": float(price_data["yes"]),
                        "yes_price": float(price_data["yes"]),
                        "no_price": float(price_data.get("no", 1.0 - float(price_data["yes"]))),
                        "token_ids": market["token_ids"],
                        "timestamp": datetime.now().isoformat()
                    }
            except Exception as e:
                print(f"⚠️ Failed to fetch data for {market_id}: {e}")
        
        return market_data

    def run_cycle(self) -> Dict[str, Any]:
        """Run one portfolio management cycle."""
        print(f"🔄 Running polymarket portfolio cycle at {datetime.now().strftime('%H:%M:%S')}")
        
        market_data = self._fetch_market_data()
        if not market_data:
            return {"status": "no_market_data", "timestamp": datetime.now().isoformat()}

        cycle_results = {
            "timestamp": datetime.now().isoformat(),
            "market_data_count": len(market_data),
            "agents_processed": 0,
            "allocations_updated": 0,
            "rebalancing_required": 0,
            "errors": []
        }

        # Process each agent
        for agent_name, agent in self.agents.items():
            try:
                account = self.accounts[agent_name]
                cycle_results["agents_processed"] += 1

                # Generate portfolio allocations for each market
                for market_id, market_info in market_data.items():
                    try:
                        allocation = agent.generate_portfolio_allocation(market_info, account)
                        if allocation:
                            # Update target allocation
                            success = account.set_target_allocation(
                                allocation["market_id"], 
                                allocation["allocation"]
                            )
                            if success:
                                cycle_results["allocations_updated"] += 1
                                print(f"✅ {agent_name}: Updated {market_id} allocation to {allocation['allocation']:.1%}")
                            else:
                                cycle_results["errors"].append(f"Failed to set allocation for {market_id}")
                    except Exception as e:
                        error_msg = f"Error processing {market_id} for {agent_name}: {e}"
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
        print(f"📊 Cycle Summary: {cycle_results['agents_processed']} agents, "
              f"{cycle_results['allocations_updated']} allocations updated, "
              f"{cycle_results['rebalancing_required']} rebalancing required")
        
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
            "last_rebalance": account.last_rebalance
        }

    def run_continuous(self, interval_minutes: int = 15, max_cycles: int = None) -> None:
        """Run continuous portfolio management cycles."""
        print(f"🚀 Starting continuous polymarket portfolio management (interval: {interval_minutes} minutes)")
        
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
    print("⚠️ create_polymarket_trading_system is deprecated, use create_polymarket_portfolio_system instead")
    return create_polymarket_portfolio_system()

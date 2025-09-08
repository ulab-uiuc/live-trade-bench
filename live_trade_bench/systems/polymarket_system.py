from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Any, Dict, List

from ..accounts import PolymarketAccount, create_polymarket_account
from ..agents.polymarket_agent import LLMPolyMarketAgent
from ..fetchers.news_fetcher import fetch_news_data
from ..fetchers.polymarket_fetcher import (
    fetch_current_market_price,
    fetch_trending_markets,
)


class PolymarketPortfolioSystem:
    def __init__(self, universe_size: int = 5) -> None:
        self.agents: Dict[str, LLMPolyMarketAgent] = {}
        self.accounts: Dict[str, PolymarketAccount] = {}
        self.universe: List[str] = []
        self.market_info: Dict[str, Dict[str, Any]] = {}
        self.cycle_count = 0
        self._init_universe(universe_size)

    def _init_universe(self, limit: int) -> None:
        markets = fetch_trending_markets(limit=limit)
        self.universe = []
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
        agent = LLMPolyMarketAgent(name, model_name)
        account = create_polymarket_account(initial_cash)
        self.agents[name] = agent
        self.accounts[name] = account

    def run_cycle(self, for_date: str | None = None) -> None:
        print(f"\n--- 🔄 Cycle {self.cycle_count} | Processing {len(self.agents)} agents ---")

        # 1. Fetch Market Data
        market_data = self._fetch_market_data()
        if not market_data:
            print("  - Market data fetch failed, skipping cycle")
            return

        # 2. Fetch News Data
        news_data = self._fetch_news_data(market_data, for_date)

        # 3. Generate Allocations
        allocations = self._generate_allocations(market_data, news_data, for_date)

        # 4. Update Accounts
        self._update_accounts(allocations, market_data)

        self.cycle_count += 1
        print("--- ✅ Cycle Finished ---")

    def _fetch_market_data(self) -> Dict[str, Dict[str, Any]]:
        print("  - Fetching market data...")
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
                print(f"    - Failed to fetch data for {market_id}: {e}")
        print(f"  - ✅ Market data fetched for {len(market_data)} markets")
        for market_id, data in list(market_data.items())[:3]:
            print(f"    - {data['question'][:40]}...: YES @ {data['yes_price']:.2%}")
        return market_data

    def _fetch_news_data(
        self, market_data: Dict[str, Any], for_date: str | None
    ) -> Dict[str, Any]:
        print("  - Fetching news data...")
        news_data_map: Dict[str, Any] = {}
        try:
            ref = (
                datetime.strptime(for_date, "%Y-%m-%d")
                if for_date
                else datetime.now()
            )
            start_date = (ref - timedelta(days=3)).strftime("%Y-%m-%d")
            end_date = ref.strftime("%Y-%m-%d")
            for market_id in list(market_data.keys())[:3]:
                question = self.market_info.get(market_id, {}).get(
                    "question", str(market_id)
                )
                query = " ".join(question.split()[:5]) if question else str(market_id)
                news_data_map[market_id] = fetch_news_data(
                    query, start_date, end_date, max_pages=1
                )
        except Exception as e:
            print(f"    - News data fetch failed: {e}")
        print("  - ✅ News data fetched")
        for market_id, news in list(news_data_map.items())[:2]:
            if news:
                print(f"    - News for {market_id}: {news[0].get('title', 'N/A')[:50]}...")
        return news_data_map

    def _generate_allocations(
        self,
        market_data: Dict[str, Any],
        news_data: Dict[str, Any],
        for_date: str | None,
    ) -> Dict[str, Dict[str, float]]:
        print("  - Generating allocations for all agents...")
        all_allocations = {}
        for agent_name, agent in self.agents.items():
            print(f"    - Processing agent: {agent_name}...")
            account = self.accounts[agent_name]
            account_data = account.get_agent_data()

            allocation = agent.generate_allocation(
                market_data, account_data, for_date, news_data=news_data
            )
            if allocation:
                all_allocations[agent_name] = allocation
                print(f"    - ✅ Allocation for {agent_name}: { {k: f'{v:.1%}' for k, v in allocation.items()} }")
            else:
                print(f"    - ⚠️ No allocation generated for {agent_name}")
                all_allocations[agent_name] = account.target_allocations
        print("  - ✅ All allocations generated")
        return all_allocations

    def _update_accounts(self, allocations: Dict[str, Dict[str, float]], price_map: Dict) -> None:
        print("  - Updating all accounts...")
        for agent_name, allocation in allocations.items():
            account = self.accounts[agent_name]

            # Rebalance account to target allocation
            try:
                account.apply_allocation(allocation, price_map=price_map)
                account.record_allocation()
                print(f"    - ✅ Account for {agent_name} updated. New Value: ${account.get_total_value():,.2f}, Cash: ${account.cash_balance:,.2f}")
            except Exception as e:
                print(f"    - ❌ Failed to update account for {agent_name}: {e}")

        print("  - ✅ All accounts updated")

    @classmethod
    def get_instance(cls):
        if not hasattr(cls, "_instance"):
            cls._instance = create_polymarket_portfolio_system()
        return cls._instance


PolymarketTradingSystem = PolymarketPortfolioSystem


def create_polymarket_portfolio_system() -> PolymarketPortfolioSystem:
    return PolymarketPortfolioSystem()

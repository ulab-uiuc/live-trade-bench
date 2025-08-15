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


class PolymarketTradingSystem:
    def __init__(self, universe_size: int = 5) -> None:
        self.agents: Dict[str, LLMPolyMarketAgent] = {}
        self.accounts: Dict[str, PolymarketAccount] = {}
        self.universe: List[Dict[str, Any]] = []
        self._init_universe(universe_size)

    def _init_universe(self, limit: int) -> None:
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
        self.agents[name] = LLMPolyMarketAgent(name, model_name)
        self.accounts[name] = create_polymarket_account(initial_cash)

    def _fetch_prices(self) -> Dict[str, Dict[str, Any]]:
        out: Dict[str, Dict[str, Any]] = {}
        for m in self.universe:
            p = fetch_current_market_price(m["token_ids"])
            if p and "yes" in p:
                out[m["id"]] = {
                    "id": m["id"],
                    "question": m["question"],
                    "category": m["category"],
                    "price": float(p["yes"]),
                    "yes_price": float(p["yes"]),
                    "no_price": float(p.get("no", 1.0 - float(p["yes"]))),
                    "token_ids": m["token_ids"],
                }
        return out

    def run_cycle(self) -> Dict[str, Any]:
        prices = self._fetch_prices()
        trades = 0
        for name, agent in self.agents.items():
            account = self.accounts[name]
            for market_id, md in prices.items():
                action = agent.generate_action(md, account)
                if action:
                    ok, _, _ = account.execute_action(action)
                    trades += int(ok)
                account.print_status()
        # return simple snapshot (you can print this upstream if desired)
        return {
            "timestamp": datetime.now().isoformat(),
            "universe": len(self.universe),
            "agents": list(self.agents.keys()),
            "trades": trades,
            "portfolios": {
                name: acc.evaluate()["portfolio_summary"]
                for name, acc in self.accounts.items()
            },
        }

    def run(self, duration_minutes: int = 10, interval: int = 60) -> None:
        end = datetime.now() + timedelta(minutes=duration_minutes)
        while datetime.now() < end:
            _ = self.run_cycle()
            time.sleep(interval)


def create_polymarket_trading_system() -> PolymarketTradingSystem:
    return PolymarketTradingSystem()

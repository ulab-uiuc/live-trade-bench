from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Dict, List

from ..accounts import StockAccount, create_stock_account
from ..fetchers.stock_fetcher import fetch_current_stock_price, fetch_trending_stocks
from .stock_agent import LLMStockAgent


class StockTradingSystem:
    def __init__(self, universe_size: int = 10) -> None:
        self.agents: Dict[str, LLMStockAgent] = {}
        self.accounts: Dict[str, StockAccount] = {}
        self.universe: List[str] = []
        self._init_universe(universe_size)

    def _init_universe(self, limit: int) -> None:
        self.universe = fetch_trending_stocks(limit=limit)

    def add_agent(
        self, name: str, initial_cash: float = 1_000.0, model_name: str = "gpt-4o-mini"
    ) -> None:
        self.agents[name] = LLMStockAgent(name, model_name)
        self.accounts[name] = create_stock_account(initial_cash)

    def _fetch_prices(self) -> Dict[str, float]:
        out: Dict[str, float] = {}
        for t in self.universe:
            p = fetch_current_stock_price(t)
            if p is not None:
                out[t] = float(p)
        return out

    def run_cycle(self) -> Dict[str, any]:
        prices = self._fetch_prices()
        trades = 0
        for name, agent in self.agents.items():
            account = self.accounts[name]
            for ticker, price in prices.items():
                data = {"id": ticker, "price": price}
                action = agent.generate_action(data, account)
                if action:
                    ok, _, _ = account.execute_action(action)
                    trades += int(ok)
            account.print_status()
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


def create_stock_trading_system() -> StockTradingSystem:
    return StockTradingSystem()

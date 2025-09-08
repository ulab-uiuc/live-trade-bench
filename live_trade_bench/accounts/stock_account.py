"""
Stock account management system (simplified)
- Single trade path via `execute_trade`
- Optional price_provider: (ticker) -> Optional[float] for live valuation
- Thin compatibility wrapper `execute_action(StockAction)`
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base_account import BaseAccount


@dataclass
class StockPosition:
    ticker: str
    quantity: float
    average_price: float
    current_price: float = 0.0

    @property
    def market_value(self) -> float:
        return self.quantity * self.current_price

    @property
    def unrealized_pnl(self) -> float:
        return self.quantity * (self.current_price - self.average_price)


@dataclass
class StockAccount(BaseAccount[StockPosition, Dict[str, Any]]):
    positions: Dict[str, StockPosition] = field(default_factory=dict)
    transactions: List[Dict[str, Any]] = field(default_factory=list)

    def get_positions(self) -> Dict[str, StockPosition]:
        return {
            ticker: pos for ticker, pos in self.positions.items() if pos.quantity > 0.01
        }

    def get_position(self, ticker: str) -> Optional[StockPosition]:
        return self.positions.get(ticker)

    def _get_position_value(self, ticker: str) -> float:
        position = self.positions.get(ticker)
        return position.market_value if position else 0.0

    def update_position_price(self, ticker: str, current_price: float) -> None:
        if ticker in self.positions:
            self.positions[ticker].current_price = current_price

    def apply_allocation(
        self,
        target_allocations: Dict[str, float],
        price_map: Optional[Dict[str, float]] = None,
    ) -> None:
        if not price_map:
            price_map = {
                ticker: pos.current_price for ticker, pos in self.positions.items()
            }

        total_value = self.get_total_value()

        # Clear existing non-cash positions
        self.cash_balance = total_value
        self.positions.clear()

        # Create new positions based on target allocations
        for ticker, target_ratio in target_allocations.items():
            if ticker == "CASH" or target_ratio <= 0:
                continue

            price = price_map.get(ticker)
            if price is None or price <= 0:
                continue

            target_value = total_value * target_ratio
            quantity = target_value / price

            self.positions[ticker] = StockPosition(
                ticker=ticker,
                quantity=quantity,
                average_price=price,
                current_price=price,
            )
            self.cash_balance -= target_value

        self.last_rebalance = datetime.now().isoformat()


def create_stock_account(initial_cash: float = 1000.0) -> StockAccount:
    return StockAccount(initial_cash=initial_cash, cash_balance=initial_cash)

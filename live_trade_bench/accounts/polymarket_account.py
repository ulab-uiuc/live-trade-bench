from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base_account import BaseAccount


@dataclass
class PolymarketPosition:
    market_id: str
    outcome: str
    quantity: float
    price: float

    @property
    def market_value(self) -> float:
        return self.quantity * self.price


@dataclass
class PolymarketAccount(BaseAccount[PolymarketPosition, Dict[str, Any]]):
    positions: Dict[str, PolymarketPosition] = field(default_factory=dict)
    transactions: List[Dict[str, Any]] = field(default_factory=list)

    def get_positions(self) -> Dict[str, PolymarketPosition]:
        return {
            ticker: pos for ticker, pos in self.positions.items() if pos.quantity > 0.01
        }

    def get_position(self, ticker: str) -> Optional[PolymarketPosition]:
        return self.positions.get(ticker)

    def _get_position_value(self, ticker: str) -> float:
        position = self.positions.get(ticker)
        return position.quantity * position.price if position else 0.0

    def apply_allocation(
        self,
        target_allocations: Dict[str, float],
        price_map: Optional[Dict[str, float]] = None,
    ) -> None:
        # Store target allocations
        self.target_allocations = target_allocations.copy()

        if not price_map:
            price_map = {ticker: pos.price for ticker, pos in self.positions.items()}

        total_value = self.get_total_value()

        # Clear existing non-cash positions
        self.cash_balance = total_value
        self.positions.clear()

        # Create new positions based on target allocations
        for ticker, target_ratio in target_allocations.items():
            if ticker == "CASH" or target_ratio <= 0:
                continue

            price_data = price_map.get(ticker)
            if not isinstance(price_data, dict):
                continue

            price = price_data.get("price")
            if price is None or price <= 0:
                continue

            target_value = total_value * target_ratio
            quantity = target_value / price

            self.positions[ticker] = PolymarketPosition(
                market_id=ticker, outcome="yes", quantity=quantity, price=price
            )
            self.cash_balance -= target_value

        self.last_rebalance = datetime.now().isoformat()


def create_polymarket_account(initial_cash: float = 500.0) -> PolymarketAccount:
    return PolymarketAccount(initial_cash=initial_cash, cash_balance=initial_cash)

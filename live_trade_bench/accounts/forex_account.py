"""
Account representation for forex portfolios.

Modeled after the stock account but keeps terminology currency-agnostic so the
same accounting logic can be reused by the portfolio system and visualization
layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base_account import BaseAccount, Position, Transaction


@dataclass
class ForexAccount(BaseAccount[Position, Transaction]):
    positions: Dict[str, Position] = field(default_factory=dict)
    transactions: List[Transaction] = field(default_factory=list)
    total_fees: float = 0.0

    def get_positions(self) -> Dict[str, Position]:
        return {
            symbol: pos for symbol, pos in self.positions.items() if abs(pos.quantity) > 0.0001
        }

    def get_position(self, symbol: str) -> Optional[Position]:
        return self.positions.get(symbol)

    def _get_position_value(self, symbol: str) -> float:
        position = self.positions.get(symbol)
        return position.market_value if position else 0.0

    def update_position_price(self, symbol: str, current_price: float) -> None:
        if symbol in self.positions:
            self.positions[symbol].current_price = current_price

    def apply_allocation(
        self,
        target_allocations: Dict[str, float],
        price_map: Optional[Dict[str, float]] = None,
        metadata_map: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> None:
        if not price_map:
            price_map = {
                symbol: pos.current_price for symbol, pos in self.positions.items()
            }

        for symbol, pos in self.positions.items():
            if symbol in price_map:
                pos.current_price = price_map[symbol]

        total_value = self.get_total_value()
        self.cash_balance = total_value
        self.positions.clear()

        for symbol, target_ratio in target_allocations.items():
            if symbol == "CASH" or target_ratio <= 0:
                continue

            price = price_map.get(symbol)
            if price is None or price <= 0:
                continue

            target_value = total_value * target_ratio
            quantity = target_value / price
            url = metadata_map.get(symbol, {}).get("url") if metadata_map else None

            self.positions[symbol] = Position(
                symbol=symbol,
                quantity=quantity,
                average_price=price,
                current_price=price,
                url=url,
            )
            self.cash_balance -= target_value

        self.last_rebalance = datetime.now().isoformat()

    def get_market_type(self) -> str:
        return "forex"

    def serialize_positions(self) -> Dict[str, Any]:
        serialized = {}
        for symbol, position in self.positions.items():
            pos_dict = {
                "symbol": position.symbol,
                "quantity": position.quantity,
                "average_price": position.average_price,
                "current_price": position.current_price,
            }
            if position.url:
                pos_dict["url"] = position.url
            serialized[symbol] = pos_dict
        return serialized

    def get_additional_account_data(self) -> Dict[str, Any]:
        return {"total_fees": self.total_fees}


def create_forex_account(initial_cash: float = 1000.0) -> ForexAccount:
    return ForexAccount(initial_cash=initial_cash, cash_balance=initial_cash)


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

from .base_account import BaseAccount, Position, Transaction


@dataclass
class StockAccount(BaseAccount[Position, Transaction]):
    positions: Dict[str, Position] = field(default_factory=dict)
    transactions: List[Transaction] = field(default_factory=list)
    total_fees: float = 0.0

    def get_positions(self) -> Dict[str, Position]:
        return {
            ticker: pos for ticker, pos in self.positions.items() if pos.quantity > 0.01
        }

    def get_position(self, ticker: str) -> Optional[Position]:
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

        # CRITICAL: Update prices of existing positions to reflect market changes
        for ticker, pos in self.positions.items():
            if ticker in price_map:
                pos.current_price = price_map[ticker]

        # Now, calculate total value based on the NEW prices
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

            # Get URL from metadata if available
            url = None
            if metadata_map and ticker in metadata_map:
                url = metadata_map[ticker].get("url")

            self.positions[ticker] = Position(
                symbol=ticker,
                quantity=quantity,
                average_price=price,
                current_price=price,
                url=url,
            )
            self.cash_balance -= target_value

        self.last_rebalance = datetime.now().isoformat()

    def get_market_type(self) -> str:
        return "stock"

    def serialize_positions(self) -> Dict[str, Any]:
        # For stock accounts, convert Position objects to dicts, similar to polymarket format
        serialized_positions = {}
        for symbol, position in self.positions.items():
            if hasattr(position, "__dict__"):
                # Convert Position object to dict
                pos_dict = {
                    "symbol": position.symbol,
                    "quantity": position.quantity,
                    "average_price": position.average_price,
                    "current_price": position.current_price,
                }
                # Include URL if available (stock-specific)
                if hasattr(position, "url") and position.url:
                    pos_dict["url"] = position.url
                serialized_positions[symbol] = pos_dict
            else:
                # Already a dict
                serialized_positions[symbol] = position
        return serialized_positions

    def get_additional_account_data(self) -> Dict[str, Any]:
        return {
            "total_fees": self.total_fees,
        }

    def _update_market_data(self) -> None:
        pass


def create_stock_account(initial_cash: float = 1000.0) -> StockAccount:
    return StockAccount(initial_cash=initial_cash, cash_balance=initial_cash)

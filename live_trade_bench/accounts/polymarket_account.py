from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from .base_account import BaseAccount, Position, Transaction


@dataclass
class PolymarketAccount(BaseAccount[Position, Transaction]):
    positions: Dict[str, Position] = field(default_factory=dict)
    transactions: List[Transaction] = field(default_factory=list)

    def get_positions(self) -> Dict[str, Position]:
        return {
            ticker: pos for ticker, pos in self.positions.items() if pos.quantity > 0.01
        }

    def get_transactions(self) -> List[Transaction]:
        return self.transactions

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

        total_value = self.get_total_value()

        # Clear existing non-cash positions
        self.cash_balance = total_value
        self.positions.clear()

        # Create new positions based on target allocations
        for symbol, target_ratio in target_allocations.items():
            if symbol == "CASH" or target_ratio <= 0:
                continue

            # Polymarket symbols are expected to be in "market_id_OUTCOME" format here
            parts = symbol.split("_")
            if len(parts) != 2:
                print(f"--- ⚠️ Skipping invalid Polymarket symbol format: {symbol} ---")
                continue
            market_id, outcome = parts[0], parts[1].lower()

            price_data = price_map.get(market_id)
            if not isinstance(price_data, dict):
                print(f"--- ⚠️ No price data found for market {market_id}. Skipping. ---")
                continue

            price = price_data.get(f"{outcome}_price")
            if price is None or price <= 0:
                print(f"--- ⚠️ No valid '{outcome}' price for market {market_id}. Skipping. ---")
                continue

            target_value = total_value * target_ratio
            quantity = target_value / price

            self.positions[symbol] = Position(
                symbol=symbol,
                quantity=quantity,
                average_price=price,
                current_price=price,
            )
            self.cash_balance -= target_value

        self.last_rebalance = datetime.now().isoformat()


def create_polymarket_account(initial_cash: float = 500.0) -> PolymarketAccount:
    return PolymarketAccount(initial_cash=initial_cash, cash_balance=initial_cash)

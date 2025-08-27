"""
Polymarket account management system (simplified)
- Single trade path (buy/sell) via `execute_trade`
- Optional price_provider callable for valuation
- Thin compatibility wrapper `execute_action(PolymarketAction)`
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .base_account import BaseAccount


@dataclass
class PolymarketPosition:
    """Polymarket position information."""

    market_id: str
    outcome: str  # "yes" or "no"
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
class PolymarketTransaction:
    """Polymarket transaction record."""

    market_id: str
    outcome: str
    quantity: float
    price: float
    transaction_type: str  # "buy" or "sell"
    timestamp: str
    commission: float = 0.0


class PolymarketAccount(BaseAccount[PolymarketPosition, PolymarketTransaction]):
    """Polymarket portfolio management account."""

    def __init__(self, cash_balance: float = 1000.0):
        super().__init__(cash_balance=cash_balance)
        self.positions: Dict[str, PolymarketPosition] = {}
        self.transactions: List[PolymarketTransaction] = []

    def _get_position_value(self, market_id: str) -> float:
        """Get current value of position in a market."""
        position = self.positions.get(market_id)
        if position:
            return position.market_value
        return 0.0

    def get_active_positions(self) -> Dict[str, Any]:
        """Get all active positions."""
        return {
            market_id: {
                "outcome": pos.outcome,
                "quantity": pos.quantity,
                "average_price": pos.average_price,
                "current_price": pos.current_price,
                "market_value": pos.market_value,
                "unrealized_pnl": pos.unrealized_pnl,
            }
            for market_id, pos in self.positions.items()
        }

    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get portfolio summary."""
        total_value = self.get_total_value()
        position_count = len(self.positions)

        return {
            "total_value": total_value,
            "cash_balance": self.cash_balance,
            "position_count": position_count,
            "target_allocations": self.target_allocations,
            "needs_rebalancing": self.needs_rebalancing(),
            "last_rebalance": self.last_rebalance,
        }

    def update_position_price(self, market_id: str, current_price: float) -> None:
        """Update current price for a position."""
        if market_id in self.positions:
            self.positions[market_id].current_price = current_price


def create_polymarket_account(initial_cash: float = 1000.0) -> PolymarketAccount:
    """Create a new polymarket account."""
    return PolymarketAccount(cash_balance=initial_cash)

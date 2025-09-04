"""
Stock account management system (simplified)
- Single trade path via `execute_trade`
- Optional price_provider: (ticker) -> Optional[float] for live valuation
- Thin compatibility wrapper `execute_action(StockAction)`
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List
import random

from .base_account import BaseAccount


@dataclass
class StockPosition:
    """Stock position information."""

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
class StockTransaction:
    """Stock transaction record."""

    ticker: str
    quantity: float
    price: float
    transaction_type: str  # "buy" or "sell"
    timestamp: str
    commission: float = 0.0


class StockAccount(BaseAccount[StockPosition, StockTransaction]):
    """Stock portfolio management account."""

    def __init__(self, cash_balance: float = 1000.0):
        super().__init__(cash_balance=cash_balance)
        self.positions: Dict[str, StockPosition] = {}
        self.transactions: List[StockTransaction] = []

    def _get_position_value(self, ticker: str) -> float:
        """Get current value of position in a stock."""
        position = self.positions.get(ticker)
        if position:
            return position.market_value
        return 0.0

    def get_active_positions(self) -> Dict[str, Any]:
        """Get all active positions."""
        return {
            ticker: {
                "quantity": pos.quantity,
                "average_price": pos.average_price,
                "current_price": pos.current_price,
                "market_value": pos.market_value,
                "unrealized_pnl": pos.unrealized_pnl,
            }
            for ticker, pos in self.positions.items()
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

    def evaluate(self) -> Dict[str, Any]:
        """Evaluate portfolio performance and return summary."""
        total_value = self.get_total_value()

        # Calculate return percentage (assuming initial cash as baseline)
        initial_cash = 1000.0  # Default initial cash for stock accounts
        return_pct = (
            ((total_value - initial_cash) / initial_cash * 100)
            if initial_cash > 0
            else 0.0
        )

        # Calculate total return (absolute dollar amount)
        total_return = total_value - initial_cash

        # Calculate unrealized P&L
        unrealized_pnl = 0.0
        for position in self.positions.values():
            unrealized_pnl += position.unrealized_pnl

        return {
            "portfolio_summary": {
                "total_value": total_value,
                "return_pct": return_pct,
                "total_return": total_return,  # Added this key
                "unrealized_pnl": unrealized_pnl,
                "cash_balance": self.cash_balance,
                "position_count": len(self.positions),
            }
        }

    def update_position_price(self, ticker: str, current_price: float) -> None:
        """Update current price for a position."""
        if ticker in self.positions:
            self.positions[ticker].current_price = current_price

    def _simulate_rebalance_to_target(self, target_allocations: Dict[str, float]):
        """
        Simulates market fluctuations and then rebalances to a target allocation.
        This provides a more realistic mock behavior.
        """
        # 1. Simulate market price fluctuation for existing positions
        for position in self.positions.values():
            # Simulate a small price change (+/- 2%)
            fluctuation = 1 + (random.random() - 0.5) * 0.04 
            position.current_price *= fluctuation

        # 2. Get the new total value after market fluctuation, and set the target
        total_value = self.get_total_value()
        self.target_allocations = target_allocations # <-- THIS IS THE FIX

        # 3. Rebalance to the new target allocation based on the new total value
        self.positions.clear()
        
        # Generate stable mock prices based on ticker hash for consistency
        mock_prices = {
            ticker: 100 + (hash(ticker) % 400) + (hash(ticker[::-1]) % 100) / 100.0
            for ticker in target_allocations.keys() if ticker != "CASH"
        }

        for ticker, ratio in target_allocations.items():
            if ticker == "CASH":
                continue
            
            # Use the newly generated mock price for rebalancing calculations
            price = mock_prices.get(ticker)
            if price is None or price == 0:
                continue

            target_value = total_value * ratio
            quantity = target_value / price
            
            self.positions[ticker] = StockPosition(
                ticker=ticker,
                quantity=quantity,
                average_price=price,
                current_price=price
            )

        # 4. Update cash balance based on the new positions
        positions_value = sum(p.market_value for p in self.positions.values())
        self.cash_balance = total_value - positions_value


def create_stock_account(initial_cash: float = 1000.0) -> StockAccount:
    """Create a new stock account."""
    return StockAccount(cash_balance=initial_cash)

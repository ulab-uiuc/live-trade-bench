"""
Stock account management system (simplified)
- Single trade path via `execute_trade`
- Optional price_provider: (ticker) -> Optional[float] for live valuation
- Thin compatibility wrapper `execute_action(StockAction)`
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Dict, List

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

    def get_current_allocations(self) -> Dict[str, float]:
        """Get current allocation percentages for all assets."""
        total_value = self.get_total_value()
        if total_value == 0:
            return {"CASH": 1.0}
        
        allocations = {"CASH": self.cash_balance / total_value}
        
        for ticker, position in self.positions.items():
            allocations[ticker] = position.market_value / total_value
            
        return allocations

    def _simulate_rebalance_to_target(self, target_allocations: Dict[str, float]):
        """
        Simulates market fluctuations, generates transactions, and then rebalances.
        """
        from datetime import datetime

        # 1. Simulate market price fluctuation for existing positions
        for position in self.positions.values():
            fluctuation = 1 + (random.random() - 0.5) * 0.04  # +/- 2%
            position.current_price *= fluctuation

        # 2. Get current allocations BEFORE rebalancing to calculate trades
        current_allocations = self.get_current_allocations()

        # 3. Generate simulated buy/sell transactions based on the difference
        # Sell transactions
        for asset, current_ratio in current_allocations.items():
            if asset == "CASH":
                continue
            target_ratio = target_allocations.get(asset, 0)
            if current_ratio > target_ratio:
                position = self.positions.get(asset)
                price = position.current_price if position else 1.0
                self.transactions.append({
                    'asset': asset, 'action': 'sell',
                    'shares': (current_ratio - target_ratio) * self.get_total_value(),
                    'price': price,
                    'timestamp': datetime.now().isoformat()
                })
        # Buy transactions
        for asset, target_ratio in target_allocations.items():
            if asset == "CASH":
                continue
            current_ratio = current_allocations.get(asset, 0)
            if target_ratio > current_ratio:
                position = self.positions.get(asset)
                # For new buys, position is None. Use a mock price consistent with rebalance logic
                price = position.current_price if position else (100 + (hash(asset) % 400) + (hash(asset[::-1]) % 100) / 100.0)
                self.transactions.append({
                    'asset': asset, 'action': 'buy',
                    'shares': (target_ratio - current_ratio) * self.get_total_value(),
                    'price': price,
                    'timestamp': datetime.now().isoformat()
                })
        
        # 4. Now, rebalance to the new target allocation
        total_value = self.get_total_value()
        self.target_allocations = target_allocations

        # 5. Rebalance to the new target allocation based on the new total value
        self.positions.clear()

        # Generate stable mock prices based on ticker hash for consistency
        mock_prices = {
            ticker: 100 + (hash(ticker) % 400) + (hash(ticker[::-1]) % 100) / 100.0
            for ticker in target_allocations.keys()
            if ticker != "CASH"
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
                current_price=price,
            )

        # 4. Update cash balance based on the new positions
        positions_value = sum(p.market_value for p in self.positions.values())
        self.cash_balance = total_value - positions_value


def create_stock_account(initial_cash: float = 1000.0) -> StockAccount:
    """Create a new stock account."""
    return StockAccount(cash_balance=initial_cash)

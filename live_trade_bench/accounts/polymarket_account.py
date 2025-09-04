"""
Polymarket account management system (simplified)
- Single trade path (buy/sell) via `execute_trade`
- Optional price_provider callable for valuation
- Thin compatibility wrapper `execute_action(PolymarketAction)`
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List
import random

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

    def __init__(self, cash_balance: float = 500.0):
        super().__init__(cash_balance=cash_balance)
        self.positions: Dict[str, PolymarketPosition] = {}
        self.transactions: List[PolymarketTransaction] = []
        self.target_allocations: Dict[str, float] = {"CASH": 1.0}

    def _get_allocations(self) -> Dict[str, float]:
        return self.target_allocations
    
    def _update_positions(self, new_allocations: Dict[str, float]):
        self.target_allocations = new_allocations

    def get_current_allocations(self) -> Dict[str, float]:
        """Get current allocation percentages for all assets."""
        total_value = self.get_total_value()
        if total_value == 0:
            return {"CASH": 1.0}
        
        allocations = {"CASH": self.cash_balance / total_value}
        
        for market_id, position in self.positions.items():
            allocations[market_id] = position.market_value / total_value
            
        return allocations

    def _simulate_rebalance_to_target(self, target_allocations: Dict[str, float]):
        """
        Simulates market fluctuations, generates transactions, and then rebalances.
        """
        from datetime import datetime
        import random

        # 1. Simulate market price fluctuation for existing positions
        for position in self.positions.values():
            fluctuation = 1 + (random.random() - 0.5) * 0.10  # +/- 5%
            position.current_price = max(0.01, min(0.99, position.current_price * fluctuation))

        # 2. Get current allocations BEFORE rebalancing to calculate trades
        current_allocations = self.get_current_allocations()

        # 3. Generate simulated buy/sell transactions based on the difference
        for asset, current_ratio in current_allocations.items():
            if asset == "CASH":
                continue
            target_ratio = target_allocations.get(asset, 0)
            if current_ratio > target_ratio:
                position = self.positions.get(asset)
                price = position.current_price if position else 0.5
                self.transactions.append({
                    'asset': asset, 'action': 'sell',
                    'shares': (current_ratio - target_ratio) * self.get_total_value(),
                    'price': price,
                    'timestamp': datetime.now().isoformat()
                })
        for asset, target_ratio in target_allocations.items():
            if asset == "CASH":
                continue
            current_ratio = current_allocations.get(asset, 0)
            if target_ratio > current_ratio:
                position = self.positions.get(asset)
                # For new buys, position is None. Use a mock price consistent with rebalance logic
                price = position.current_price if position else (hash(asset) % 100) / 100.0
                self.transactions.append({
                    'asset': asset, 'action': 'buy',
                    'shares': (target_ratio - current_ratio) * self.get_total_value(),
                    'price': price,
                    'timestamp': datetime.now().isoformat()
                })
        
        # 4. Now, rebalance to the new target allocation
        total_value = self.get_total_value()
        self.target_allocations = target_allocations
        self.positions.clear()
        
        mock_prices = {
            market: (hash(market) % 100) / 100.0
            for market in target_allocations.keys() if market != "CASH"
        }

        for market_id, ratio in target_allocations.items():
            if market_id == "CASH": continue
            
            price = mock_prices.get(market_id, 0.5)
            if price <= 0: continue

            target_value = total_value * ratio
            quantity = target_value / price
            
            self.positions[market_id] = PolymarketPosition(
                market_id=market_id, outcome="yes", quantity=quantity,
                average_price=price, current_price=price
            )

        # 5. Update cash balance
        positions_value = sum(p.market_value for p in self.positions.values())
        self.cash_balance = total_value - positions_value

    def _get_position_value(self, ticker: str) -> float:
        """Get current value of a position."""
        position = self.positions.get(ticker)
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

    def evaluate(self) -> Dict[str, Any]:
        """Evaluate portfolio performance and return summary."""
        total_value = self.get_total_value()

        # Calculate return percentage (assuming initial cash as baseline)
        initial_cash = 500.0  # Default initial cash
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

    def update_position_price(self, market_id: str, current_price: float) -> None:
        """Update current price for a position."""
        if market_id in self.positions:
            self.positions[market_id].current_price = current_price


def create_polymarket_account(initial_cash: float = 500.0) -> PolymarketAccount:
    """Create a new polymarket account."""
    return PolymarketAccount(cash_balance=initial_cash)

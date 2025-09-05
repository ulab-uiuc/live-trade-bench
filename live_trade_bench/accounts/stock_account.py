"""
Stock account management system (simplified)
- Single trade path via `execute_trade`
- Optional price_provider: (ticker) -> Optional[float] for live valuation
- Thin compatibility wrapper `execute_action(StockAction)`
"""

from __future__ import annotations

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
        Execute real rebalancing to target allocation with real market prices.
        """
        from datetime import datetime

        # Get real market prices using fetcher (lazy import to avoid startup blocking)
        real_prices = {}

        for ticker in target_allocations.keys():
            if ticker == "CASH":
                continue
            try:
                from ..fetchers.stock_fetcher import StockFetcher

                fetcher = StockFetcher()
                price = fetcher.fetch("stock_price", ticker=ticker)
                if price:
                    real_prices[ticker] = price
                    print(f"✅ REAL: Fetched {ticker} price: ${price:.2f}")
                else:
                    print(f"⚠️ FALLBACK: API returned null price for {ticker}")
                    print(f"⚠️ FALLBACK: Using mock price $100.00 for {ticker}")
                    real_prices[ticker] = 100.0
            except Exception as e:
                print(f"⚠️ FALLBACK: Could not fetch real price for {ticker}: {e}")
                print(f"⚠️ FALLBACK: Using mock price $100.00 for {ticker}")
                real_prices[ticker] = 100.0

        # Update existing positions with real prices
        for ticker, position in self.positions.items():
            if ticker in real_prices:
                position.current_price = real_prices[ticker]

        # Get current allocations and total value
        current_allocations = self.get_current_allocations()
        total_value = self.get_total_value()

        # Generate real rebalancing transactions
        for asset, current_ratio in current_allocations.items():
            if asset == "CASH":
                continue
            target_ratio = target_allocations.get(asset, 0)
            if (
                abs(current_ratio - target_ratio) > 0.01
            ):  # Only trade if difference > 1%
                price = real_prices.get(asset, 100.0)
                value_diff = (target_ratio - current_ratio) * total_value
                action = "buy" if value_diff > 0 else "sell"
                self.transactions.append(
                    {
                        "asset": asset,
                        "action": action,
                        "shares": abs(value_diff),
                        "price": price,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        # Execute rebalancing with real prices
        self.target_allocations = target_allocations
        self.positions.clear()

        for ticker, ratio in target_allocations.items():
            if ticker == "CASH" or ratio <= 0:
                continue

            price = real_prices.get(ticker, 100.0)
            target_value = total_value * ratio
            quantity = target_value / price

            self.positions[ticker] = StockPosition(
                ticker=ticker,
                quantity=quantity,
                average_price=price,
                current_price=price,
            )

        # Update cash balance
        positions_value = sum(p.market_value for p in self.positions.values())
        self.cash_balance = total_value - positions_value


def create_stock_account(initial_cash: float = 1000.0) -> StockAccount:
    """Create a new stock account."""
    return StockAccount(cash_balance=initial_cash)

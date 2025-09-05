"""
Polymarket account management system (simplified)
- Single trade path (buy/sell) via `execute_trade`
- Optional price_provider callable for valuation
- Thin compatibility wrapper `execute_action(PolymarketAction)`
"""

from __future__ import annotations

from dataclasses import dataclass
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
        Execute real rebalancing to target allocation with real market prices.
        """
        from datetime import datetime

        # Get real Polymarket prices using fetcher (lazy import to avoid startup blocking)
        market_ids = [m for m in target_allocations.keys() if m != "CASH"]
        real_prices = {}

        if market_ids:
            try:
                from ..fetchers.polymarket_fetcher import PolymarketFetcher

                fetcher = PolymarketFetcher()

                # Get trending markets to find token_ids for our market_ids
                markets = fetcher.fetch("trending_markets", limit=50)
                market_to_tokens = {}

                for market in markets:
                    if market.get("id") in market_ids and market.get("token_ids"):
                        market_to_tokens[market["id"]] = market["token_ids"]

                print(
                    f"📡 Found token mappings for {len(market_to_tokens)}/{len(market_ids)} markets"
                )

                # Get prices for each market using its first token
                for market_id in market_ids:
                    if market_id in market_to_tokens:
                        token_ids = market_to_tokens[market_id]
                        if token_ids and len(token_ids) > 0:
                            first_token = token_ids[0]
                            price_data = fetcher.fetch(
                                "token_price", token_id=first_token
                            )
                            if price_data and isinstance(price_data, dict):
                                raw_price = price_data.get("price")
                                if raw_price is not None and isinstance(
                                    raw_price, (int, float)
                                ):
                                    real_price = max(0.01, min(0.99, float(raw_price)))
                                    real_prices[market_id] = real_price
                                    print(
                                        f"✅ REAL: Fetched {market_id} via token {first_token}: ${real_price:.3f}"
                                    )
                                    continue

                    # Fallback for this market
                    print(
                        f"⚠️ FALLBACK: Could not get token mapping or price for market {market_id}"
                    )
                    print(f"⚠️ FALLBACK: Using mock price $0.50 for {market_id}")
                    real_prices[market_id] = 0.5

            except Exception as e:
                print(f"⚠️ FALLBACK: Error in Polymarket price fetching: {e}")
                print(
                    f"⚠️ FALLBACK: Using mock price $0.50 for all {len(market_ids)} markets"
                )
                for market_id in market_ids:
                    real_prices[market_id] = 0.5

        # Update existing positions with real prices
        for market_id, position in self.positions.items():
            if market_id in real_prices:
                position.current_price = real_prices[market_id]

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
                price = real_prices.get(asset, 0.5)
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

        for market_id, ratio in target_allocations.items():
            if market_id == "CASH" or ratio <= 0:
                continue

            price = real_prices.get(market_id, 0.5)
            target_value = total_value * ratio
            quantity = target_value / price

            self.positions[market_id] = PolymarketPosition(
                market_id=market_id,
                outcome="yes",
                quantity=quantity,
                average_price=price,
                current_price=price,
            )

        # Update cash balance
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

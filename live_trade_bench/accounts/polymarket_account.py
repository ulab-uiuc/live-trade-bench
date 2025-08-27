"""
Polymarket account management system (simplified)
- Single trade path (buy/sell) via `execute_trade`
- Optional price_provider callable for valuation
- Thin compatibility wrapper `execute_action(PolymarketAction)`
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

from .base_account import BaseAccount


@dataclass
class PolymarketPosition:
    """Polymarket position with market_id, outcome, quantity, avg_price, cost_basis."""

    market_id: str
    outcome: str  # "yes" or "no"
    quantity: float
    avg_price: float
    cost_basis: float = field(init=False)
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self) -> None:
        """Post-initialization processing"""
        if self.quantity < 0:
            raise ValueError(f"Invalid quantity: {self.quantity}")
        if self.avg_price < 0:
            raise ValueError(f"Invalid avg_price: {self.avg_price}")
        if not self.market_id:
            raise ValueError("Market ID cannot be empty")
        if self.outcome.lower() not in ("yes", "no"):
            raise ValueError(f"Invalid outcome: {self.outcome}")

        self.cost_basis = self.quantity * self.avg_price
        self.outcome = self.outcome.lower()

    def apply_buy(self, price: float, qty: float) -> None:
        """Apply a buy to this position."""
        if qty <= 0:
            raise ValueError(f"Invalid buy quantity: {qty}")

        # Update average price
        total_cost = self.cost_basis + (qty * price)
        total_quantity = self.quantity + qty
        self.avg_price = total_cost / total_quantity
        self.quantity = total_quantity
        self.cost_basis = total_cost
        self.last_updated = datetime.now().isoformat()

    def apply_sell(self, qty: float) -> None:
        """Apply a sell to this position."""
        if qty <= 0:
            raise ValueError(f"Invalid sell quantity: {qty}")
        if qty > self.quantity:
            raise ValueError(f"Insufficient quantity: have {self.quantity}, sell {qty}")

        self.quantity -= qty
        self.cost_basis = self.avg_price * self.quantity
        self.last_updated = datetime.now().isoformat()


@dataclass
class PolymarketTransaction:
    """Immutable record of a trade."""

    market_id: str
    outcome: str  # "yes" or "no"
    action: str  # "buy" or "sell"
    quantity: float
    price: float  # 0-1
    timestamp: str
    commission: float = 0.0
    notes: str = ""

    def __post_init__(self) -> None:
        if self.action.lower() not in ("buy", "sell"):
            raise ValueError(f"Invalid action: {self.action}")
        if not (0.0 <= self.price <= 1.0):
            raise ValueError(f"Invalid price: {self.price} (must be 0-1)")
        if self.quantity <= 0:
            raise ValueError(f"Invalid quantity: {self.quantity}")
        if not self.market_id:
            raise ValueError("Market ID cannot be empty")
        if self.outcome.lower() not in ("yes", "no"):
            raise ValueError(f"Invalid outcome: {self.outcome}")

        self.action = self.action.lower()
        self.outcome = self.outcome.lower()

    @property
    def position_key(self) -> str:
        return f"{self.market_id}_{self.outcome}"

    @property
    def cash_effect(self) -> float:
        """
        Signed cash flow for the account (positive = cash in).
        Buy -> negative (price*qty + commission); Sell -> positive (price*qty - commission).
        """
        gross = self.quantity * self.price
        return (
            (gross - self.commission)
            if self.action == "sell"
            else -(gross + self.commission)
        )


# ----------------------------------------------
# Polymarket Account Implementation
# ----------------------------------------------


@dataclass
class PolymarketAccount(BaseAccount[PolymarketPosition, PolymarketTransaction]):
    """Polymarket portfolio management account."""

    positions: Dict[str, PolymarketPosition] = field(default_factory=dict)
    price_provider: Optional[Any] = None  # For real-time pricing

    def _key(self, market_id: str, outcome: str) -> str:
        """Generate position key."""
        return f"{market_id}_{outcome}"

    def _current_price(self, market_id: str, outcome: str, fallback: float) -> float:
        """Get current price for a market outcome."""
        if self.price_provider:
            try:
                return self.price_provider.get_price(market_id, outcome)
            except Exception:
                pass
        return fallback

    def get_total_value(self) -> float:
        """Get total account value (cash + positions)."""
        position_value = sum(
            pos.quantity
            * self._current_price(pos.market_id, pos.outcome, pos.avg_price)
            for pos in self.positions.values()
            if pos.quantity > 0
        )
        return self.cash_balance + position_value

    def _get_position_value(self, ticker: str) -> float:
        """Get current value of a position."""
        # For polymarket, ticker format is "market_id_outcome"
        if "_" not in ticker:
            return 0.0

        market_id, outcome = ticker.rsplit("_", 1)
        pos = self.positions.get(self._key(market_id, outcome))
        if not pos or pos.quantity <= 0:
            return 0.0
        return pos.quantity * self._current_price(market_id, outcome, pos.avg_price)

    def get_active_positions(self) -> Dict[str, Any]:
        """Get all active positions."""
        return {
            self._key(pos.market_id, pos.outcome): pos
            for pos in self.positions.values()
            if pos.quantity > 0
        }

    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get portfolio summary with allocations."""
        active = self.get_active_positions()
        total_value = self.get_total_value()

        if not active:
            return {
                "total_value": total_value,
                "cash_balance": self.cash_balance,
                "positions": {},
                "allocations": {},
                "target_allocations": self.target_allocations,
                "needs_rebalancing": self.needs_rebalancing(),
            }

        positions_summary = {}
        current_allocations = {}

        for key, pos in active.items():
            current_price = self._current_price(
                pos.market_id, pos.outcome, pos.avg_price
            )
            current_value = pos.quantity * current_price
            current_ratio = current_value / total_value if total_value > 0 else 0.0

            positions_summary[key] = {
                "market_id": pos.market_id,
                "outcome": pos.outcome,
                "quantity": pos.quantity,
                "avg_price": pos.avg_price,
                "current_price": current_price,
                "current_value": current_value,
                "current_allocation": current_ratio,
                "target_allocation": self.get_target_allocation(key),
                "allocation_difference": self.get_allocation_difference(key),
            }

            current_allocations[key] = current_ratio

        return {
            "total_value": total_value,
            "cash_balance": self.cash_balance,
            "positions": positions_summary,
            "allocations": current_allocations,
            "target_allocations": self.target_allocations,
            "needs_rebalancing": self.needs_rebalancing(),
            "last_rebalance": self.last_rebalance,
        }

    def execute_rebalancing(self, rebalance_plan: Dict[str, Any]) -> bool:
        """Execute portfolio rebalancing based on plan."""
        if rebalance_plan.get("status") != "rebalancing_required":
            return False

        actions = rebalance_plan.get("actions", [])
        success_count = 0

        for action in actions:
            ticker = action["ticker"]
            value_adjustment = action["value_adjustment"]
            action_type = action["action"]

            if action_type == "buy" and value_adjustment > 0:
                if self._execute_buy_adjustment(ticker, value_adjustment):
                    success_count += 1
            elif action_type == "sell" and value_adjustment < 0:
                if self._execute_sell_adjustment(ticker, abs(value_adjustment)):
                    success_count += 1

        return success_count == len(actions)

    def _execute_buy_adjustment(self, ticker: str, value_adjustment: float) -> bool:
        """Execute buy adjustment for rebalancing."""
        if "_" not in ticker:
            return False

        market_id, outcome = ticker.rsplit("_", 1)
        current_price = self._current_price(market_id, outcome, 0.0)
        if current_price <= 0:
            return False

        quantity = value_adjustment / current_price
        if quantity <= 0:
            return False

        # Check if we can afford this
        total_cost = value_adjustment + self.calculate_commission(
            current_price, quantity
        )
        if total_cost > self.cash_balance:
            return False

        # Execute the buy
        self._add_position(market_id, outcome, quantity, current_price)
        self.cash_balance -= total_cost
        return True

    def _execute_sell_adjustment(self, ticker: str, value_adjustment: float) -> bool:
        """Execute sell adjustment for rebalancing."""
        if "_" not in ticker:
            return False

        market_id, outcome = ticker.rsplit("_", 1)
        current_price = self._current_price(market_id, outcome, 0.0)
        if current_price <= 0:
            return False

        quantity = value_adjustment / current_price
        if quantity <= 0:
            return False

        # Check if we have enough shares
        key = self._key(market_id, outcome)
        pos = self.positions.get(key)
        if not pos or pos.quantity < quantity:
            return False

        # Execute the sell
        self._reduce_position(market_id, outcome, quantity)
        proceeds = value_adjustment - self.calculate_commission(current_price, quantity)
        self.cash_balance += proceeds
        return True

    def _add_position(
        self, market_id: str, outcome: str, quantity: float, price: float
    ) -> None:
        """Add to existing position or create new one."""
        key = self._key(market_id, outcome)
        if key in self.positions:
            pos = self.positions[key]
            # Update average price
            total_cost = pos.cost_basis + (quantity * price)
            total_quantity = pos.quantity + quantity
            pos.avg_price = total_cost / total_quantity
            pos.quantity = total_quantity
            pos.cost_basis = total_cost
        else:
            self.positions[key] = PolymarketPosition(
                market_id=market_id,
                outcome=outcome,
                quantity=quantity,
                avg_price=price,
                cost_basis=quantity * price,
                last_updated=datetime.now().isoformat(),
            )

    def _reduce_position(self, market_id: str, outcome: str, quantity: float) -> None:
        """Reduce existing position."""
        key = self._key(market_id, outcome)
        if key in self.positions:
            pos = self.positions[key]
            if pos.quantity >= quantity:
                pos.quantity -= quantity
                pos.cost_basis = pos.avg_price * pos.quantity
                pos.last_updated = datetime.now().isoformat()

                # Remove position if quantity becomes 0
                if pos.quantity <= 0:
                    del self.positions[key]

    # ----- Backward Compatibility Methods -----
    def evaluate(self) -> Dict[str, Any]:
        """Backward compatibility - now returns portfolio summary."""
        return self.get_portfolio_summary()

    def get_trading_summary(self) -> Dict[str, Any]:
        """Backward compatibility - simplified trading summary."""
        return {
            "total_trades": 0,  # No longer tracking individual trades
            "last_trade": None,
            "commission_paid": 0.0,
        }


def create_polymarket_account(initial_cash: float) -> PolymarketAccount:
    """Create a new Polymarket account."""
    return PolymarketAccount(initial_cash)

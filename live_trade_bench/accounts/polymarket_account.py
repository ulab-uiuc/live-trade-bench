"""
Polymarket account management system (simplified)
- Single trade path (buy/sell) via `execute_trade`
- Optional price_provider callable for valuation
- Thin compatibility wrapper `execute_action(PolymarketAction)`
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple

from .base_account import BaseAccount

if TYPE_CHECKING:
    from .action import PolymarketAction


# ----------------------------- Data Models -----------------------------


@dataclass
class PolymarketPosition:
    """Position in a Polymarket market."""

    market_id: str
    outcome: str  # "yes" or "no"
    quantity: float
    avg_price: float  # 0-1
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self) -> None:
        if self.quantity < 0:
            raise ValueError(f"Invalid quantity: {self.quantity}")
        if not (0.0 <= self.avg_price <= 1.0):
            raise ValueError(f"Invalid avg_price: {self.avg_price} (must be 0-1)")
        if not self.market_id:
            raise ValueError("Market ID cannot be empty")
        if self.outcome.lower() not in ("yes", "no"):
            raise ValueError(f"Invalid outcome: {self.outcome}")

        self.outcome = self.outcome.lower()

    @property
    def position_key(self) -> str:
        return f"{self.market_id}_{self.outcome}"

    @property
    def cost_basis(self) -> float:
        return self.quantity * self.avg_price

    def apply_buy(self, price: float, qty: float) -> None:
        if not (0.0 <= price <= 1.0) or qty <= 0:
            raise ValueError("Price must be 0-1 and quantity must be positive")
        total_cost = self.cost_basis + price * qty
        self.quantity += qty
        self.avg_price = total_cost / self.quantity if self.quantity > 0 else price
        self.last_updated = datetime.now().isoformat()

    def apply_sell(self, qty: float) -> None:
        if qty <= 0:
            raise ValueError("Quantity must be positive")
        if qty > self.quantity:
            raise ValueError(f"Insufficient position: have {self.quantity}, sell {qty}")
        self.quantity -= qty
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


# ------------------------------- Account -------------------------------


@dataclass
class PolymarketAccount(BaseAccount):
    """
    Polymarket trading account.

    Attributes expected from BaseAccount:
      - cash_balance: float
      - initial_cash: float
      - commission_rate: float
      - calculate_commission(price, quantity) -> float
      - get_basic_summary() -> Dict[str, Any]
    """

    positions: Dict[str, PolymarketPosition] = field(default_factory=dict)
    transactions: List[PolymarketTransaction] = field(default_factory=list)

    # Optional: provide a callable to fetch current prices: (market_id, outcome) -> Optional[float]
    price_provider: Optional[Callable[[str, str], Optional[float]]] = None

    # ----------- Convenience -----------

    def _key(self, market_id: str, outcome: str) -> str:
        return f"{market_id}_{outcome.lower()}"

    def get_active_positions(self) -> Dict[str, PolymarketPosition]:
        return {k: p for k, p in self.positions.items() if p.quantity > 0}

    # ----------- Trading -----------

    def can_afford(self, price: float, quantity: float) -> Tuple[bool, str]:
        commission = self.calculate_commission(price, quantity)
        total_cost = price * quantity + commission
        return (
            (True, "Sufficient funds")
            if total_cost <= self.cash_balance
            else (
                False,
                f"Insufficient funds: need ${total_cost:.2f}, have ${self.cash_balance:.2f}",
            )
        )

    def can_sell(
        self, market_id: str, outcome: str, quantity: float
    ) -> Tuple[bool, str]:
        pos = self.positions.get(self._key(market_id, outcome))
        if not pos or pos.quantity == 0:
            return False, f"No position in {market_id} {outcome}"
        if pos.quantity < quantity:
            return False, f"Insufficient position: have {pos.quantity}, sell {quantity}"
        return True, "Sufficient position"

    def execute_action(
        self, action: "PolymarketAction", notes: str = ""
    ) -> Tuple[bool, str, Optional[PolymarketTransaction]]:
        """
        Execute a PolymarketAction. Returns (success, message, transaction).
        """
        market_id = action.market_id
        outcome = action.outcome.lower()
        trade_action = action.action.lower()
        price = action.price
        quantity = action.quantity
        notes = notes or f"PolymarketAction from {action.timestamp}"
        
        if trade_action not in {"buy", "sell"}:
            return False, f"Invalid action: {trade_action}", None

        if trade_action == "buy":
            ok, why = self.can_afford(price, quantity)
            if not ok:
                return False, why, None
        else:
            ok, why = self.can_sell(market_id, outcome, quantity)
            if not ok:
                return False, why, None

        commission = self.calculate_commission(price, quantity)
        tx = PolymarketTransaction(
            market_id=market_id,
            outcome=outcome,
            action=trade_action,
            quantity=quantity,
            price=price,
            commission=commission,
            timestamp=datetime.now().isoformat(),
            notes=notes,
        )

        # Apply cash and position changes
        try:
            self.cash_balance += tx.cash_effect  # signed effect

            key = self._key(market_id, outcome)
            if trade_action == "buy":
                if key in self.positions:
                    self.positions[key].apply_buy(price, quantity)
                else:
                    self.positions[key] = PolymarketPosition(
                        market_id=market_id,
                        outcome=outcome,
                        quantity=quantity,
                        avg_price=price,
                    )
            else:  # sell
                self.positions[key].apply_sell(quantity)
                if self.positions[key].quantity <= 0:
                    del self.positions[key]

            self.transactions.append(tx)
            return (
                True,
                f"{trade_action.title()} {quantity} {outcome} @ ${price:.3f} ({market_id})",
                tx,
            )

        except Exception as e:
            return False, f"Trade failed: {e}", None

    # ----------- Valuation / Reporting -----------

    def _current_price(self, market_id: str, outcome: str, fallback: float) -> float:
        if self.price_provider is None:
            return fallback
        try:
            p = self.price_provider(market_id, outcome.lower())
            return fallback if p is None else p
        except Exception:
            return fallback

    def evaluate(self) -> Dict[str, Any]:
        """
        Evaluate portfolio with current prices (from price_provider if set, else avg_price).
        """
        active = self.get_active_positions()
        if not active:
            total = self.cash_balance
            total_return = total - self.initial_cash
            return {
                "total_asset_value": total,
                "portfolio_assets": {},
                "active_positions": 0,
                "portfolio_summary": {
                    "cash_balance": self.cash_balance,
                    "position_value": 0.0,
                    "total_value": total,
                    "unrealized_pnl": 0.0,
                    "total_return": total_return,
                    "return_pct": (total_return / self.initial_cash * 100.0)
                    if self.initial_cash > 0
                    else 0.0,
                },
                "markets": [],
                "account_summary": self.get_trading_summary(),
            }

        assets: Dict[str, Dict[str, Any]] = {}
        position_value = 0.0
        total_unrealized = 0.0

        for key, pos in active.items():
            cur_price = self._current_price(
                pos.market_id, pos.outcome, fallback=pos.avg_price
            )
            cur_val = pos.quantity * cur_price
            basis = pos.cost_basis
            upl = cur_val - basis

            assets[key] = {
                "market_id": pos.market_id,
                "outcome": pos.outcome,
                "quantity": pos.quantity,
                "avg_price": pos.avg_price,
                "current_price": cur_price,
                "cost_basis": basis,
                "current_value": cur_val,
                "unrealized_pnl": upl,
                "unrealized_pnl_pct": (upl / basis * 100.0) if basis > 0 else 0.0,
                "portfolio_weight": 0.0,  # set below
                "last_updated": pos.last_updated,
            }

            position_value += cur_val
            total_unrealized += upl

        total_value = self.cash_balance + position_value
        total_return = total_value - self.initial_cash
        return_pct = (
            (total_return / self.initial_cash * 100.0) if self.initial_cash > 0 else 0.0
        )

        if total_value > 0:
            for k in assets:
                assets[k]["portfolio_weight"] = (
                    assets[k]["current_value"] / total_value * 100.0
                )

        return {
            "total_asset_value": total_value,
            "portfolio_assets": assets,
            "active_positions": len(active),
            "portfolio_summary": {
                "cash_balance": self.cash_balance,
                "position_value": position_value,
                "total_value": total_value,
                "unrealized_pnl": total_unrealized,
                "total_return": total_return,
                "return_pct": return_pct,
            },
            "markets": list({p.market_id for p in active.values()}),
            "account_summary": self.get_trading_summary(),
        }

    def _calculate_total_value_direct(self) -> float:
        """Calculate total value directly without going through evaluate() to avoid recursion."""
        active = self.get_active_positions()
        position_value = 0.0

        for pos in active.values():
            current_price = self._current_price(
                pos.market_id, pos.outcome, fallback=pos.avg_price
            )
            position_value += pos.quantity * current_price

        return self.cash_balance + position_value

    def get_total_value(self) -> float:
        return self.evaluate()["portfolio_summary"]["total_value"]

    def get_trading_summary(self) -> Dict[str, Any]:
        buys = [t for t in self.transactions if t.action == "buy"]
        sells = [t for t in self.transactions if t.action == "sell"]
        total_commission = sum(t.commission for t in self.transactions)

        base = self.get_basic_summary()

        # Calculate total_return and return_percentage without recursion
        current_total_value = self._calculate_total_value_direct()
        total_return = current_total_value - self.initial_cash
        return_percentage = (
            (total_return / self.initial_cash * 100.0) if self.initial_cash > 0 else 0.0
        )

        return {
            **base,
            "total_return": total_return,
            "return_percentage": return_percentage,
            "total_trades": len(self.transactions),
            "buy_trades": len(buys),
            "sell_trades": len(sells),
            "total_commission": total_commission,
            "active_positions": len(self.get_active_positions()),
            "markets_traded": len({t.market_id for t in self.transactions}),
        }

    def print_status(self) -> None:
        print(
            f"💰 Cash: ${self.cash_balance:.2f} | Positions: {len(self.get_active_positions())} | Total: ${self.get_total_value():.2f}"
        )


# --------------------------- Convenience ---------------------------


def create_polymarket_account(
    initial_cash: float = 1000.0,
    commission_rate: float = 0.01,
    price_provider: Optional[Callable[[str, str], Optional[float]]] = None,
) -> PolymarketAccount:
    """
    Create a new PolymarketAccount. Provide `price_provider` to enable live valuation.
    """
    return PolymarketAccount(
        cash_balance=initial_cash,
        commission_rate=commission_rate,
        price_provider=price_provider,
    )

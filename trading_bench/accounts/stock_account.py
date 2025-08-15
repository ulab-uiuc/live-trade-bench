"""
Stock account management system (simplified)
- Single trade path via `execute_trade`
- Optional price_provider: (ticker) -> Optional[float] for live valuation
- Thin compatibility wrapper `execute_action(StockAction)`
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple

from .base_account import BaseAccount

if TYPE_CHECKING:
    from .action import StockAction


# ----------------------------- Data Models -----------------------------


@dataclass
class StockPosition:
    """Long/short position for a stock ticker."""

    ticker: str
    quantity: float
    avg_price: float
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self) -> None:
        if self.quantity < 0:
            raise ValueError(f"Invalid quantity: {self.quantity}")
        if self.avg_price <= 0:
            raise ValueError(f"Invalid avg_price: {self.avg_price}")
        if not self.ticker:
            raise ValueError("Ticker cannot be empty")

    @property
    def cost_basis(self) -> float:
        return self.quantity * self.avg_price

    def apply_buy(self, price: float, qty: float) -> None:
        if price <= 0 or qty <= 0:
            raise ValueError("Price and quantity must be positive")
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
class StockTransaction:
    """Immutable record of a trade."""

    ticker: str
    action: str  # "buy" or "sell"
    quantity: float
    price: float
    timestamp: str
    commission: float = 0.0
    notes: str = ""

    def __post_init__(self) -> None:
        if self.action.lower() not in ("buy", "sell"):
            raise ValueError(f"Invalid action: {self.action}")
        if self.price <= 0:
            raise ValueError(f"Invalid price: {self.price}")
        if self.quantity <= 0:
            raise ValueError(f"Invalid quantity: {self.quantity}")
        if not self.ticker:
            raise ValueError("Ticker cannot be empty")
        self.action = self.action.lower()

    @property
    def cash_effect(self) -> float:
        """
        Signed cash flow (positive = cash in).
        Buy -> -(price*qty + commission); Sell -> +(price*qty - commission).
        """
        gross = self.quantity * self.price
        return (
            (gross - self.commission)
            if self.action == "sell"
            else -(gross + self.commission)
        )


# ------------------------------- Account -------------------------------


@dataclass
class StockAccount(BaseAccount):
    """
    Stock trading account.

    BaseAccount is expected to provide:
      - cash_balance: float
      - initial_cash: float
      - commission_rate: float
      - calculate_commission(price, quantity) -> float
      - get_basic_summary() -> Dict[str, Any]
    """

    positions: Dict[str, StockPosition] = field(default_factory=dict)
    transactions: List[StockTransaction] = field(default_factory=list)

    # Optional callable to fetch current prices: (ticker) -> Optional[float]
    price_provider: Optional[Callable[[str], Optional[float]]] = None

    # ----------- Convenience -----------

    def get_active_positions(self) -> Dict[str, StockPosition]:
        return {t: p for t, p in self.positions.items() if p.quantity > 0}

    def print_status(self) -> None:
        print(
            f"💰 Cash: ${self.cash_balance:.2f} | Positions: {len(self.get_active_positions())} | Total: ${self.get_total_value():.2f}"
        )

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

    def can_sell(self, ticker: str, quantity: float) -> Tuple[bool, str]:
        pos = self.positions.get(ticker)
        if not pos or pos.quantity == 0:
            return False, f"No position in {ticker}"
        if pos.quantity < quantity:
            return False, f"Insufficient position: have {pos.quantity}, sell {quantity}"
        return True, "Sufficient position"

    def execute_action(
        self, action: "StockAction", notes: str = ""
    ) -> Tuple[bool, str, Optional[StockTransaction]]:
        """
        Execute a StockAction. Returns (success, message, transaction).
        """
        from .action import StockAction

        if not isinstance(action, StockAction):
            return False, "Invalid action: must be a StockAction instance", None

        ticker = action.ticker
        trade_action = action.action.lower()
        price = action.price
        quantity = action.quantity
        notes = notes or f"StockAction from {action.timestamp}"
        
        if trade_action not in {"buy", "sell"}:
            return False, f"Invalid action: {trade_action}", None

        if trade_action == "buy":
            ok, why = self.can_afford(price, quantity)
            if not ok:
                return False, why, None
        else:
            ok, why = self.can_sell(ticker, quantity)
            if not ok:
                return False, why, None

        commission = self.calculate_commission(price, quantity)
        tx = StockTransaction(
            ticker=ticker,
            action=trade_action,
            quantity=quantity,
            price=price,
            commission=commission,
            timestamp=datetime.now().isoformat(),
            notes=notes,
        )

        try:
            # cash
            self.cash_balance += tx.cash_effect

            # position
            if trade_action == "buy":
                if ticker in self.positions:
                    self.positions[ticker].apply_buy(price, quantity)
                else:
                    self.positions[ticker] = StockPosition(
                        ticker=ticker, quantity=quantity, avg_price=price
                    )
            else:  # sell
                self.positions[ticker].apply_sell(quantity)
                if self.positions[ticker].quantity <= 0:
                    del self.positions[ticker]

            # record
            self.transactions.append(tx)
            return True, f"{trade_action.title()} {quantity} {ticker} @ ${price:.3f}", tx

        except Exception as e:
            return False, f"Trade failed: {e}", None

    # ----------- Valuation / Reporting -----------

    def _current_price(self, ticker: str, fallback: float) -> float:
        if self.price_provider is None:
            return fallback
        try:
            p = self.price_provider(ticker)
            return fallback if p is None or p <= 0 else float(p)
        except Exception:
            return fallback

    def evaluate(self) -> Dict[str, Any]:
        """
        Evaluate portfolio using `price_provider` if set, else falls back to avg_price.
        """
        active = self.get_active_positions()
        if not active:
            total = self.cash_balance
            total_ret = total - self.initial_cash
            return {
                "total_asset_value": total,
                "portfolio_assets": {},
                "active_positions": 0,
                "portfolio_summary": {
                    "cash_balance": self.cash_balance,
                    "stock_value": 0.0,
                    "total_value": total,
                    "unrealized_pnl": 0.0,
                    "total_return": total_ret,
                    "return_pct": (total_ret / self.initial_cash * 100.0)
                    if self.initial_cash > 0
                    else 0.0,
                },
                "tickers": [],
                "account_summary": self.get_trading_summary(),
            }

        assets: Dict[str, Dict[str, Any]] = {}
        stock_value = 0.0
        total_unrealized = 0.0

        for t, pos in active.items():
            cur_price = self._current_price(t, fallback=pos.avg_price)
            cur_val = pos.quantity * cur_price
            basis = pos.cost_basis
            upl = cur_val - basis

            assets[t] = {
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

            stock_value += cur_val
            total_unrealized += upl

        total_value = self.cash_balance + stock_value
        total_ret = total_value - self.initial_cash
        return_pct = (
            (total_ret / self.initial_cash * 100.0) if self.initial_cash > 0 else 0.0
        )

        if total_value > 0:
            for t in assets:
                assets[t]["portfolio_weight"] = (
                    assets[t]["current_value"] / total_value * 100.0
                )

        return {
            "total_asset_value": total_value,
            "portfolio_assets": assets,
            "active_positions": len(active),
            "portfolio_summary": {
                "cash_balance": self.cash_balance,
                "stock_value": stock_value,
                "total_value": total_value,
                "unrealized_pnl": total_unrealized,
                "total_return": total_ret,
                "return_pct": return_pct,
            },
            "tickers": list(active.keys()),
            "account_summary": self.get_trading_summary(),
        }

    def _calculate_total_value_direct(self) -> float:
        """Calculate total value directly without going through evaluate() to avoid recursion."""
        active = self.get_active_positions()
        position_value = 0.0

        for pos in active.values():
            current_price = self._current_price(pos.ticker, fallback=pos.avg_price)
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
        # We need total_value but calling get_total_value() would cause recursion via evaluate()
        # So we'll calculate it directly from cash + position values
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
        }


# --------------------------- Convenience ---------------------------


def create_stock_account(
    initial_cash: float = 100_000.0,
    commission_rate: float = 0.001,
    price_provider: Optional[Callable[[str], Optional[float]]] = None,
) -> StockAccount:
    """Create a new StockAccount. Provide `price_provider` to enable live valuation."""
    return StockAccount(
        cash_balance=initial_cash,
        commission_rate=commission_rate,
        price_provider=price_provider,
    )

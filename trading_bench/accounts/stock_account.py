"""
Stock account management system inheriting from BaseAccount
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from .base_account import BaseAccount

if TYPE_CHECKING:
    from .action import StockAction


@dataclass
class StockPosition:
    """Stock position information"""

    ticker: str
    quantity: float
    avg_price: float
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self):
        """Validate position fields"""
        if self.quantity < 0:
            raise ValueError(f"Invalid quantity: {self.quantity}")
        if self.avg_price <= 0:
            raise ValueError(f"Invalid avg_price: {self.avg_price}")
        if not self.ticker:
            raise ValueError("Ticker cannot be empty")

    @property
    def cost_basis(self) -> float:
        """Total cost basis of the position"""
        return self.quantity * self.avg_price

    def update_buy(self, price: float, quantity: float) -> None:
        """Update position after buy transaction"""
        if price <= 0 or quantity <= 0:
            raise ValueError("Price and quantity must be positive")

        total_cost = self.cost_basis + (price * quantity)
        self.quantity += quantity
        self.avg_price = total_cost / self.quantity if self.quantity > 0 else price
        self.last_updated = datetime.now().isoformat()

    def update_sell(self, quantity: float) -> None:
        """Update position after sell transaction"""
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        if self.quantity < quantity:
            raise ValueError(f"Insufficient position: {self.quantity} < {quantity}")

        self.quantity -= quantity
        self.last_updated = datetime.now().isoformat()


@dataclass
class StockTransaction:
    """Trading transaction record"""

    ticker: str
    action: str  # "buy" or "sell"
    quantity: float
    price: float
    timestamp: str
    commission: float = 0.0
    notes: str = ""

    def __post_init__(self):
        """Validate transaction fields"""
        if self.action.lower() not in ("buy", "sell"):
            raise ValueError(f"Invalid action: {self.action}")
        if self.price <= 0:
            raise ValueError(f"Invalid price: {self.price}")
        if self.quantity <= 0:
            raise ValueError(f"Invalid quantity: {self.quantity}")
        if not self.ticker:
            raise ValueError("Ticker cannot be empty")

    @property
    def total_value(self) -> float:
        """Total transaction value including commission"""
        base_value = self.quantity * self.price
        if self.action.lower() == "buy":
            return base_value + self.commission
        else:
            return base_value - self.commission


@dataclass
class StockAccount(BaseAccount):
    """Stock trading account with integrated portfolio evaluation"""

    positions: Dict[str, StockPosition] = field(default_factory=dict)
    transactions: List[StockTransaction] = field(default_factory=list)

    def _fetch_current_price(self, ticker: str) -> Optional[float]:
        """Try to fetch current price using improved fetcher methods"""
        try:
            # Use the new current price method from fetcher
            from ..fetchers.stock_fetcher import get_current_stock_price
            
            price = get_current_stock_price(ticker)
            if price and price > 0:
                return price
                
        except Exception as e:
            print(f"⚠️ Real-time price fetch failed for {ticker}: {e}")

        # Fallback to original method
        try:
            from ..fetchers.stock_fetcher import fetch_stock_data

            data = fetch_stock_data(ticker, resolution="D")
            if data:
                latest_date = max(data.keys())
                current_price = data[latest_date].get("close")
                if current_price and current_price > 0:
                    return current_price
        except:
            pass
        return None

    def get_total_value(self) -> float:
        """Get total account value (cash + stock positions)"""
        active_positions = self.get_active_positions()
        stock_value = 0.0

        for ticker, position in active_positions.items():
            # Try to fetch current price, fallback to avg price
            current_price = self._fetch_current_price(ticker)
            if current_price is None:
                current_price = position.avg_price
            stock_value += position.quantity * current_price

        return self.cash_balance + stock_value

    def can_afford(
        self, ticker: str, price: float, quantity: float
    ) -> Tuple[bool, str]:
        """Check if account has sufficient funds for purchase"""
        commission = self.calculate_commission(price, quantity)
        total_cost = price * quantity + commission

        if total_cost <= self.cash_balance:
            return True, f"Can buy {quantity} shares of {ticker}"
        else:
            return (
                False,
                f"Insufficient funds: need ${total_cost:.2f}, available ${self.cash_balance:.2f}",
            )

    def can_sell(self, ticker: str, quantity: float) -> Tuple[bool, str]:
        """Check if account has sufficient position for sale"""
        position = self.positions.get(ticker)
        if not position or position.quantity == 0:
            return False, f"No position in {ticker}"

        if position.quantity >= quantity:
            return True, f"Can sell {quantity} shares of {ticker}"
        else:
            return (
                False,
                f"Insufficient position: hold {position.quantity} shares, trying to sell {quantity}",
            )

    def execute_action(
        self, action: "StockAction", notes: str = ""
    ) -> Tuple[bool, str, Optional[StockTransaction]]:
        """
        Execute a StockAction

        Args:
            action: StockAction instance containing trade details
            notes: Optional notes for the transaction

        Returns:
            Tuple of (success, message, transaction)
        """
        # Import here to avoid circular imports
        from .action import StockAction

        if not isinstance(action, StockAction):
            return False, "Invalid action: must be a StockAction instance", None

        return self.execute_trade(
            ticker=action.ticker,
            action=action.action,
            price=action.price,
            quantity=action.quantity,
            notes=notes or f"StockAction from {action.timestamp}",
        )

    def execute_trade(
        self, ticker: str, action: str, price: float, quantity: float, notes: str = ""
    ) -> Tuple[bool, str, Optional[StockTransaction]]:
        """
        Execute trade transaction (legacy method for backward compatibility)

        Args:
            ticker: Stock ticker symbol
            action: "buy" or "sell"
            price: Price per share
            quantity: Number of shares
            notes: Optional notes

        Returns:
            Tuple of (success, message, transaction)
        """
        action = action.lower()
        commission = self.calculate_commission(price, quantity)

        # Validate transaction
        if action == "buy":
            can_afford, reason = self.can_afford(ticker, price, quantity)
            if not can_afford:
                return False, reason, None
        elif action == "sell":
            can_sell, reason = self.can_sell(ticker, quantity)
            if not can_sell:
                return False, reason, None
        else:
            return False, f"Invalid action: {action}", None

        # Create transaction record
        transaction = StockTransaction(
            ticker=ticker,
            action=action,
            quantity=quantity,
            price=price,
            timestamp=datetime.now().isoformat(),
            commission=commission,
            notes=notes,
        )

        # Execute transaction
        try:
            if action == "buy":
                self.cash_balance -= transaction.total_value

                if ticker in self.positions:
                    self.positions[ticker].update_buy(price, quantity)
                else:
                    self.positions[ticker] = StockPosition(ticker, quantity, price)

            elif action == "sell":
                self.cash_balance += transaction.total_value
                self.positions[ticker].update_sell(quantity)

            self.transactions.append(transaction)
            return (
                True,
                f"Successfully {action} {quantity} shares of {ticker} @ ${price:.2f}",
                transaction,
            )

        except Exception as e:
            return False, f"Trade failed: {str(e)}", None

    def get_active_positions(self) -> Dict[str, StockPosition]:
        """Get active positions (quantity > 0)"""
        return {
            ticker: pos for ticker, pos in self.positions.items() if pos.quantity > 0
        }

    def get_trading_summary(self) -> Dict[str, Any]:
        """Get basic trading summary"""
        buy_trades = [t for t in self.transactions if t.action == "buy"]
        sell_trades = [t for t in self.transactions if t.action == "sell"]
        total_commission = sum(t.commission for t in self.transactions)

        base_summary = self.get_basic_summary()

        return {
            **base_summary,
            "total_trades": len(self.transactions),
            "buy_trades": len(buy_trades),
            "sell_trades": len(sell_trades),
            "total_commission": total_commission,
            "active_positions": len(self.get_active_positions()),
        }

    def evaluate(self) -> Dict[str, Any]:
        """
        Evaluate account portfolio with current prices and calculate portfolio value

        Returns:
            Dictionary containing portfolio evaluation results
        """
        active = self.get_active_positions()

        # If no active positions, return basic cash-only portfolio
        if not active:
            cash_value = self.cash_balance
            total_return = cash_value - self.initial_cash
            return_pct = (
                (total_return / self.initial_cash * 100)
                if self.initial_cash > 0
                else 0.0
            )

            return {
                "total_asset_value": cash_value,
                "portfolio_assets": {},
                "active_positions": 0,
                "portfolio_summary": {
                    "cash_balance": cash_value,
                    "stock_value": 0.0,
                    "total_value": cash_value,
                    "unrealized_pnl": 0.0,
                    "total_return": total_return,
                    "return_pct": return_pct,
                },
                "tickers": [],
                "account_summary": self.get_trading_summary(),
                "price_fetch_success": 0,
            }

        # Try to fetch current prices, fallback to avg price if fetch fails
        prices = {}
        price_fetch_count = 0

        for ticker, position in active.items():
            current_price = self._fetch_current_price(ticker)
            if current_price:
                prices[ticker] = current_price
                price_fetch_count += 1
            else:
                # Fallback to average price
                prices[ticker] = position.avg_price

        # Calculate portfolio assets and values
        assets: Dict[str, Dict[str, float]] = {}
        stock_value = 0.0
        total_unrealized_pnl = 0.0

        for ticker, position in active.items():
            current_price = prices[ticker]
            current_value = position.quantity * current_price
            cost_basis = position.cost_basis
            unrealized_pnl = current_value - cost_basis

            assets[ticker] = {
                "quantity": position.quantity,
                "avg_price": position.avg_price,
                "current_price": current_price,
                "cost_basis": cost_basis,
                "current_value": current_value,
                "unrealized_pnl": unrealized_pnl,
                "unrealized_pnl_pct": (unrealized_pnl / cost_basis * 100.0)
                if cost_basis > 0
                else 0.0,
                "portfolio_weight": 0.0,  # Will be calculated below
                "last_updated": position.last_updated,
            }

            stock_value += current_value
            total_unrealized_pnl += unrealized_pnl

        # Calculate total portfolio value
        total_value = self.cash_balance + stock_value
        total_return = total_value - self.initial_cash
        return_pct = (
            (total_return / self.initial_cash * 100) if self.initial_cash > 0 else 0.0
        )

        # Calculate portfolio weights
        if total_value > 0:
            for ticker in assets:
                assets[ticker]["portfolio_weight"] = (
                    assets[ticker]["current_value"] / total_value * 100.0
                )

        # Portfolio summary
        portfolio_summary = {
            "cash_balance": self.cash_balance,
            "stock_value": stock_value,
            "total_value": total_value,
            "unrealized_pnl": total_unrealized_pnl,
            "total_return": total_return,
            "return_pct": return_pct,
        }

        return {
            "total_asset_value": total_value,
            "portfolio_assets": assets,
            "active_positions": len(active),
            "portfolio_summary": portfolio_summary,
            "tickers": list(active.keys()),
            "account_summary": self.get_trading_summary(),
            "price_fetch_success": price_fetch_count,
        }


# Convenience functions
def create_stock_account(
    initial_cash: float = 100000.0, commission_rate: float = 0.001
) -> StockAccount:
    """Create new stock account"""
    return StockAccount(cash_balance=initial_cash, commission_rate=commission_rate)


# Legacy function for backward compatibility
def eval_account(account: StockAccount) -> Dict[str, Any]:
    """Legacy function - use account.evaluate() instead"""
    return account.evaluate()

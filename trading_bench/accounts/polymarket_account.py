"""
Polymarket account management system inheriting from BaseAccount
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from .base_account import BaseAccount

if TYPE_CHECKING:
    from .action import PolymarketAction


@dataclass
class PolymarketPosition:
    """Polymarket position information"""

    market_id: str
    outcome: str  # "yes" or "no"
    quantity: float
    avg_price: float  # Average price (0-1 range)
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self):
        """Validate position fields"""
        if self.quantity < 0:
            raise ValueError(f"Invalid quantity: {self.quantity}")
        if not (0 <= self.avg_price <= 1):
            raise ValueError(f"Invalid avg_price: {self.avg_price} (must be 0-1)")
        if not self.market_id:
            raise ValueError("Market ID cannot be empty")
        if self.outcome.lower() not in ("yes", "no"):
            raise ValueError(f"Invalid outcome: {self.outcome}")

    @property
    def position_key(self) -> str:
        """Unique key for this position"""
        return f"{self.market_id}_{self.outcome.lower()}"

    @property
    def cost_basis(self) -> float:
        """Total cost basis of the position"""
        return self.quantity * self.avg_price

    def update_buy(self, price: float, quantity: float) -> None:
        """Update position after buy transaction"""
        if not (0 <= price <= 1) or quantity <= 0:
            raise ValueError("Price must be 0-1 and quantity must be positive")

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
class PolymarketTransaction:
    """Polymarket trading transaction record"""

    market_id: str
    outcome: str  # "yes" or "no"
    action: str  # "buy" or "sell"
    quantity: float
    price: float  # 0-1 range
    timestamp: str
    commission: float = 0.0
    notes: str = ""

    def __post_init__(self):
        """Validate transaction fields"""
        if self.action.lower() not in ("buy", "sell"):
            raise ValueError(f"Invalid action: {self.action}")
        if not (0 <= self.price <= 1):
            raise ValueError(f"Invalid price: {self.price} (must be 0-1)")
        if self.quantity <= 0:
            raise ValueError(f"Invalid quantity: {self.quantity}")
        if not self.market_id:
            raise ValueError("Market ID cannot be empty")
        if self.outcome.lower() not in ("yes", "no"):
            raise ValueError(f"Invalid outcome: {self.outcome}")

    @property
    def position_key(self) -> str:
        """Unique key for this position"""
        return f"{self.market_id}_{self.outcome.lower()}"

    @property
    def total_value(self) -> float:
        """Total transaction value including commission"""
        base_value = self.quantity * self.price
        if self.action.lower() == "buy":
            return base_value + self.commission
        else:
            return base_value - self.commission


@dataclass
class PolymarketAccount(BaseAccount):
    """Polymarket trading account with integrated portfolio evaluation"""

    positions: Dict[str, PolymarketPosition] = field(default_factory=dict)
    transactions: List[PolymarketTransaction] = field(default_factory=list)

    def _fetch_current_price(self, market_id: str, outcome: str) -> Optional[float]:
        """Try to fetch current price, return None if failed"""
        try:
            from ..fetchers.polymarket_fetcher import PolymarketFetcher
            fetcher = PolymarketFetcher()
            
            # Get market data using correct method name
            market_data = fetcher.fetch_market_details(market_id)
            if market_data and "outcomes" in market_data:
                for outcome_data in market_data["outcomes"]:
                    if outcome_data.get("outcome", "").lower() == outcome.lower():
                        # Try different price field names
                        price = outcome_data.get("price") or outcome_data.get("current_price")
                        if price is not None and 0 <= price <= 1:
                            return price
        except:
            pass
        return None

    def get_total_value(self) -> float:
        """Get total account value (cash + polymarket positions)"""
        active_positions = self.get_active_positions()
        position_value = 0.0

        for position_key, position in active_positions.items():
            # Try to fetch current price, fallback to avg price
            current_price = self._fetch_current_price(
                position.market_id, position.outcome
            )
            if current_price is None:
                current_price = position.avg_price
            position_value += position.quantity * current_price

        return self.cash_balance + position_value

    def can_afford(
        self, market_id: str, price: float, quantity: float
    ) -> Tuple[bool, str]:
        """Check if account has sufficient funds for purchase"""
        commission = self.calculate_commission(price, quantity)
        total_cost = price * quantity + commission

        if total_cost <= self.cash_balance:
            return True, f"Can buy {quantity} shares in {market_id}"
        else:
            return (
                False,
                f"Insufficient funds: need ${total_cost:.2f}, available ${self.cash_balance:.2f}",
            )

    def can_sell(
        self, market_id: str, outcome: str, quantity: float
    ) -> Tuple[bool, str]:
        """Check if account has sufficient position for sale"""
        position_key = f"{market_id}_{outcome.lower()}"
        position = self.positions.get(position_key)

        if not position or position.quantity == 0:
            return False, f"No position in {market_id} {outcome}"

        if position.quantity >= quantity:
            return True, f"Can sell {quantity} shares of {market_id} {outcome}"
        else:
            return (
                False,
                f"Insufficient position: hold {position.quantity} shares, trying to sell {quantity}",
            )

    def execute_action(
        self, action: "PolymarketAction", notes: str = ""
    ) -> Tuple[bool, str, Optional[PolymarketTransaction]]:
        """
        Execute a PolymarketAction

        Args:
            action: PolymarketAction instance containing trade details
            notes: Optional notes for the transaction

        Returns:
            Tuple of (success, message, transaction)
        """
        # Import here to avoid circular imports
        from .action import PolymarketAction

        if not isinstance(action, PolymarketAction):
            return False, "Invalid action: must be a PolymarketAction instance", None

        return self.execute_trade(
            market_id=action.market_id,
            outcome=action.outcome,
            action=action.action,
            price=action.price,
            quantity=action.quantity,
            notes=notes or f"PolymarketAction from {action.timestamp}",
        )

    def execute_trade(
        self,
        market_id: str,
        outcome: str,
        action: str,
        price: float,
        quantity: float,
        notes: str = "",
    ) -> Tuple[bool, str, Optional[PolymarketTransaction]]:
        """
        Execute trade transaction

        Args:
            market_id: Market identifier
            outcome: "yes" or "no"
            action: "buy" or "sell"
            price: Price per share (0-1 range)
            quantity: Number of shares
            notes: Optional notes

        Returns:
            Tuple of (success, message, transaction)
        """
        action = action.lower()
        outcome = outcome.lower()
        position_key = f"{market_id}_{outcome}"
        commission = self.calculate_commission(price, quantity)

        # Validate transaction
        if action == "buy":
            can_afford, reason = self.can_afford(market_id, price, quantity)
            if not can_afford:
                return False, reason, None
        elif action == "sell":
            can_sell, reason = self.can_sell(market_id, outcome, quantity)
            if not can_sell:
                return False, reason, None
        else:
            return False, f"Invalid action: {action}", None

        # Create transaction record
        transaction = PolymarketTransaction(
            market_id=market_id,
            outcome=outcome,
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

                if position_key in self.positions:
                    self.positions[position_key].update_buy(price, quantity)
                else:
                    self.positions[position_key] = PolymarketPosition(
                        market_id=market_id,
                        outcome=outcome,
                        quantity=quantity,
                        avg_price=price,
                    )

            elif action == "sell":
                self.cash_balance += transaction.total_value
                self.positions[position_key].update_sell(quantity)

            self.transactions.append(transaction)
            return (
                True,
                f"Successfully {action} {quantity} shares of {market_id} {outcome} @ ${price:.3f}",
                transaction,
            )

        except Exception as e:
            return False, f"Trade failed: {str(e)}", None

    def get_active_positions(self) -> Dict[str, PolymarketPosition]:
        """Get active positions (quantity > 0)"""
        return {key: pos for key, pos in self.positions.items() if pos.quantity > 0}

    def get_trading_summary(self) -> Dict[str, Any]:
        """Get basic trading summary"""
        buy_trades = [t for t in self.transactions if t.action == "buy"]
        sell_trades = [t for t in self.transactions if t.action == "sell"]
        total_commission = sum(t.commission for t in self.transactions)

        # Group by markets
        markets_traded = set()
        for transaction in self.transactions:
            markets_traded.add(transaction.market_id)

        base_summary = self.get_basic_summary()

        return {
            **base_summary,
            "total_trades": len(self.transactions),
            "buy_trades": len(buy_trades),
            "sell_trades": len(sell_trades),
            "total_commission": total_commission,
            "active_positions": len(self.get_active_positions()),
            "markets_traded": len(markets_traded),
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
                    "position_value": 0.0,
                    "total_value": cash_value,
                    "unrealized_pnl": 0.0,
                    "total_return": total_return,
                    "return_pct": return_pct,
                },
                "markets": [],
                "account_summary": self.get_trading_summary(),
                "price_fetch_success": 0,
            }

        # Try to fetch current prices, fallback to avg price if fetch fails
        prices = {}
        price_fetch_count = 0

        for position_key, position in active.items():
            current_price = self._fetch_current_price(
                position.market_id, position.outcome
            )
            if current_price is not None:
                prices[position_key] = current_price
                price_fetch_count += 1
            else:
                # Fallback to average price
                prices[position_key] = position.avg_price

        # Calculate portfolio assets and values
        assets: Dict[str, Dict[str, Any]] = {}
        position_value = 0.0
        total_unrealized_pnl = 0.0

        for position_key, position in active.items():
            current_price = prices[position_key]
            current_value = position.quantity * current_price
            cost_basis = position.cost_basis
            unrealized_pnl = current_value - cost_basis

            assets[position_key] = {
                "market_id": position.market_id,
                "outcome": position.outcome,
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

            position_value += current_value
            total_unrealized_pnl += unrealized_pnl

        # Calculate total portfolio value
        total_value = self.cash_balance + position_value
        total_return = total_value - self.initial_cash
        return_pct = (
            (total_return / self.initial_cash * 100) if self.initial_cash > 0 else 0.0
        )

        # Calculate portfolio weights
        if total_value > 0:
            for position_key in assets:
                assets[position_key]["portfolio_weight"] = (
                    assets[position_key]["current_value"] / total_value * 100.0
                )

        # Portfolio summary
        portfolio_summary = {
            "cash_balance": self.cash_balance,
            "position_value": position_value,
            "total_value": total_value,
            "unrealized_pnl": total_unrealized_pnl,
            "total_return": total_return,
            "return_pct": return_pct,
        }

        # Get unique markets
        markets_list = list(set(pos.market_id for pos in active.values()))

        return {
            "total_asset_value": total_value,
            "portfolio_assets": assets,
            "active_positions": len(active),
            "portfolio_summary": portfolio_summary,
            "markets": markets_list,
            "account_summary": self.get_trading_summary(),
            "price_fetch_success": price_fetch_count,
        }


# Convenience functions
def create_polymarket_account(
    initial_cash: float = 1000.0, commission_rate: float = 0.01
) -> PolymarketAccount:
    """Create new polymarket account (higher commission rate for prediction markets)"""
    return PolymarketAccount(cash_balance=initial_cash, commission_rate=commission_rate)


# Legacy function for backward compatibility
def eval_polymarket_account(account: PolymarketAccount) -> Dict[str, Any]:
    """Legacy function - use account.evaluate() instead"""
    return account.evaluate()

"""
Base account management system - Abstract base for all account types
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Generic, Optional, TypeVar

# Generic type for different position and transaction types
PositionType = TypeVar("PositionType")
TransactionType = TypeVar("TransactionType")


@dataclass
class BaseAccount(ABC, Generic[PositionType, TransactionType]):
    """Abstract base class for portfolio management accounts"""

    cash_balance: float
    initial_cash: float = field(init=False)
    commission_rate: float = 0.001
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # Portfolio allocation tracking
    target_allocations: Dict[str, float] = field(default_factory=dict)
    last_rebalance: Optional[str] = None

    def __post_init__(self) -> None:
        """Post-initialization processing"""
        if self.cash_balance < 0:
            raise ValueError(f"Invalid cash_balance: {self.cash_balance}")
        self.initial_cash = self.cash_balance

    @property
    def account_age_days(self) -> int:
        """Get account age in days"""
        return (datetime.now() - datetime.fromisoformat(self.created_at)).days

    @property
    def total_return(self) -> float:
        """Calculate total return"""
        current_value = self.get_total_value()
        return current_value - self.initial_cash

    @property
    def return_percentage(self) -> float:
        """Calculate return percentage"""
        if self.initial_cash <= 0:
            return 0.0
        return (self.total_return / self.initial_cash) * 100

    # ----- Portfolio Management Methods -----
    def set_target_allocation(self, ticker: str, target_ratio: float) -> bool:
        """Set target allocation for an asset."""
        if not (0.0 <= target_ratio <= 1.0):
            print(f"⚠️ Invalid allocation ratio: {target_ratio} for {ticker}")
            return False

        self.target_allocations[ticker] = target_ratio
        self.last_rebalance = datetime.now().isoformat()
        return True

    def get_target_allocation(self, ticker: str) -> float:
        """Get target allocation for an asset."""
        return self.target_allocations.get(ticker, 0.0)

    def get_current_allocation(self, ticker: str) -> float:
        """Get current allocation for an asset."""
        total_value = self.get_total_value()
        if total_value <= 0:
            return 0.0

        position_value = self._get_position_value(ticker)
        return position_value / total_value

    def get_allocation_difference(self, ticker: str) -> float:
        """Get difference between target and current allocation."""
        target = self.get_target_allocation(ticker)
        current = self.get_current_allocation(ticker)
        return target - current

    def needs_rebalancing(self, threshold: float = 0.05) -> bool:
        """Check if portfolio needs rebalancing."""
        for ticker in self.target_allocations:
            if abs(self.get_allocation_difference(ticker)) > threshold:
                return True
        return False

    def rebalance_portfolio(self) -> Dict[str, Any]:
        """Rebalance portfolio to match target allocations."""
        if not self.needs_rebalancing():
            return {"status": "no_rebalancing_needed"}

        rebalance_actions = []
        total_value = self.get_total_value()

        for ticker, target_ratio in self.target_allocations.items():
            current_ratio = self.get_current_allocation(ticker)
            difference = target_ratio - current_ratio

            if abs(difference) > 0.01:  # 1% threshold
                target_value = total_value * target_ratio
                current_value = total_value * current_ratio
                value_adjustment = target_value - current_value

                rebalance_actions.append(
                    {
                        "ticker": ticker,
                        "current_ratio": current_ratio,
                        "target_ratio": target_ratio,
                        "value_adjustment": value_adjustment,
                        "action": "buy" if value_adjustment > 0 else "sell",
                    }
                )

        self.last_rebalance = datetime.now().isoformat()
        return {
            "status": "rebalancing_required",
            "actions": rebalance_actions,
            "timestamp": self.last_rebalance,
        }

    # ----- Abstract Methods -----
    @abstractmethod
    def get_total_value(self) -> float:
        """Get total account value (cash + positions)"""
        pass

    @abstractmethod
    def _get_position_value(self, ticker: str) -> float:
        """Get current value of a position."""
        pass

    @abstractmethod
    def get_active_positions(self) -> Dict[str, Any]:
        """Get all active positions."""
        pass

    def calculate_commission(self, price: float, quantity: float) -> float:
        """Calculate commission for a trade."""
        return price * quantity * self.commission_rate

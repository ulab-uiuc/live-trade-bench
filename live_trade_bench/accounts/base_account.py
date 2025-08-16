"""
Base account management system - Abstract base for all account types
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, Tuple, TypeVar

# Generic type for different position types
PositionType = TypeVar("PositionType")
TransactionType = TypeVar("TransactionType")
ActionType = TypeVar("ActionType")


@dataclass
class BaseAccount(ABC):
    """Abstract base class for trading accounts"""

    cash_balance: float
    initial_cash: float = field(init=False)
    commission_rate: float = 0.001
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self):
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

    @abstractmethod
    def get_total_value(self) -> float:
        """Get total account value (cash + positions)"""
        pass

    @abstractmethod
    def can_afford(
        self, ticker: str, price: float, quantity: float
    ) -> Tuple[bool, str]:
        """Check if account can afford a purchase"""
        pass

    @abstractmethod
    def can_sell(self, ticker: str, quantity: float) -> Tuple[bool, str]:
        """Check if account can sell a position"""
        pass

    @abstractmethod
    def execute_action(
        self, action: ActionType, notes: str = ""
    ) -> Tuple[bool, str, Optional[TransactionType]]:
        """Execute a trading action"""
        pass

    @abstractmethod
    def get_active_positions(self) -> Dict[str, PositionType]:
        """Get all active positions"""
        pass

    @abstractmethod
    def get_trading_summary(self) -> Dict[str, Any]:
        """Get trading statistics summary"""
        pass

    @abstractmethod
    def evaluate(self) -> Dict[str, Any]:
        """Evaluate account and return detailed portfolio information"""
        pass

    def calculate_commission(self, price: float, quantity: float) -> float:
        """Calculate commission for a trade"""
        return price * quantity * self.commission_rate

    def get_basic_summary(self) -> Dict[str, Any]:
        """Get basic account summary (common to all account types)"""
        return {
            "cash_balance": self.cash_balance,
            "initial_cash": self.initial_cash,
            "account_age_days": self.account_age_days,
            "commission_rate": self.commission_rate,
            "created_at": self.created_at,
            # Note: total_return and return_percentage not included here to avoid recursion
            # They should be calculated separately where needed
        }

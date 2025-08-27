"""
Base account management system - Abstract base for all account types
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Generic, Optional, TypeVar

# Generic type for different position and transaction types
PositionType = TypeVar("PositionType")
TransactionType = TypeVar("TransactionType")


@dataclass
class BaseAccount(ABC, Generic[PositionType, TransactionType]):
    """Base portfolio management account."""

    cash_balance: float = 0.0
    target_allocations: Dict[str, float] = field(default_factory=dict)
    last_rebalance: Optional[str] = None

    def set_target_allocation(self, ticker: str, target_ratio: float) -> bool:
        """Set target allocation for an asset."""
        if not (0.0 <= target_ratio <= 1.0):
            print(f"⚠️ Invalid allocation ratio {target_ratio} for {ticker}")
            return False

        self.target_allocations[ticker] = target_ratio
        return True

    def get_target_allocation(self, ticker: str) -> float:
        """Get target allocation for an asset."""
        return self.target_allocations.get(ticker, 0.0)

    def get_current_allocation(self, ticker: str) -> float:
        """Get current allocation for an asset."""
        total_value = self.get_total_value()
        if total_value == 0:
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

    def get_total_value(self) -> float:
        """Get total portfolio value."""
        total = self.cash_balance
        for ticker in self.target_allocations:
            total += self._get_position_value(ticker)
        return total

    @abstractmethod
    def _get_position_value(self, ticker: str) -> float:
        """Get current value of position in an asset."""
        ...

    @abstractmethod
    def get_active_positions(self) -> Dict[str, Any]:
        """Get all active positions."""
        ...

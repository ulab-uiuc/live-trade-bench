"""
Base account management system - Abstract base for all account types
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Generic, Optional, TypeVar, List

# Generic type for different position and transaction types
PositionType = TypeVar("PositionType")
TransactionType = TypeVar("TransactionType")


@dataclass
class BaseAccount(ABC, Generic[PositionType, TransactionType]):
    """Base portfolio management account."""

    cash_balance: float = 0.0
    target_allocations: Dict[str, float] = field(default_factory=dict)
    allocation_history: List[Dict[str, Any]] = field(default_factory=list)
    last_rebalance: Optional[str] = None

    def _record_allocation_snapshot(self):
        """Records the current portfolio state to allocation_history."""
        from datetime import datetime

        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "total_value": self.get_total_value(),
            "allocations": self.get_portfolio_value_breakdown().get("current_allocations", {})
        }
        self.allocation_history.append(snapshot)
        print(f"📸 Recorded portfolio snapshot. History now has {len(self.allocation_history)} entries.")

    def set_target_allocation(self, ticker: str, target_ratio: float) -> bool:
        """Set target allocation for an asset (including CASH)."""
        if not (0.0 <= target_ratio <= 1.0):
            print(f"⚠️ Invalid allocation ratio {target_ratio} for {ticker}")
            return False

        self.target_allocations[ticker] = target_ratio
        return True

    def get_target_allocation(self, ticker: str) -> float:
        """Get target allocation for an asset (including CASH)."""
        return self.target_allocations.get(ticker, 0.0)

    def get_current_allocation(self, ticker: str) -> float:
        """Get current allocation for an asset (including CASH)."""
        total_value = self.get_total_value()
        if total_value == 0:
            return 0.0

        if ticker == "CASH":
            return self.cash_balance / total_value

        position_value = self._get_position_value(ticker)
        return position_value / total_value

    def get_allocation_difference(self, ticker: str) -> float:
        """Get difference between target and current allocation."""
        target = self.get_target_allocation(ticker)
        current = self.get_current_allocation(ticker)
        return target - current

    def needs_rebalancing(self, threshold: float = 0.05) -> bool:
        """Check if portfolio needs rebalancing."""
        # Check all assets including CASH
        for ticker in self.target_allocations:
            if abs(self.get_allocation_difference(ticker)) > threshold:
                return True
        return False

    def get_total_value(self) -> float:
        """Get total portfolio value."""
        total = self.cash_balance
        for ticker in self.target_allocations:
            if ticker != "CASH":  # Don't double-count cash
                total += self._get_position_value(ticker)
        return total

    def get_portfolio_value_breakdown(self) -> Dict[str, Any]:
        """Get detailed portfolio value breakdown."""
        total_value = self.get_total_value()
        cash_value = self.cash_balance
        positions_value = total_value - cash_value

        # Calculate current allocations
        current_allocations = {}
        for ticker in self.target_allocations:
            current_allocations[ticker] = self.get_current_allocation(ticker)

        return {
            "total_value": total_value,
            "cash_value": cash_value,
            "positions_value": positions_value,
            "cash_allocation": cash_value / total_value if total_value > 0 else 0.0,
            "positions_allocation": positions_value / total_value
            if total_value > 0
            else 0.0,
            "current_allocations": current_allocations,
            "target_allocations": self.target_allocations.copy(),
        }

    @abstractmethod
    def _simulate_rebalance_to_target(self, target_allocations: Dict[str, float]):
        """
        Simulates rebalancing to a target allocation.
        This method MUST be implemented by subclasses to handle specific logic
        for price fluctuation, transaction generation, and position updates.
        """
        pass

    def _update_positions(self, new_allocations: Dict[str, float]):
        """
        Updates the portfolio holdings to match the new_allocations.
        This is a placeholder for the actual position update logic.
        """
        # In a real system, this would involve buying/selling assets
        # to adjust holdings to match new_allocations.
        print(f"Simulating position update to: {new_allocations}")
        # For demonstration, we'll just print the new allocations
        # self.cash_balance -= (sum(new_allocations.values()) - 1.0) * self.get_total_value() # Example cash adjustment

    @abstractmethod
    def _get_position_value(self, ticker: str) -> float:
        """Get current value of position in an asset."""
        ...

    @abstractmethod
    def get_active_positions(self) -> Dict[str, Any]:
        """Get all active positions."""
        ...

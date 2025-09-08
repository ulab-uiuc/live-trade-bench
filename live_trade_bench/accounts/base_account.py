"""
Base account management system - Abstract base for all account types
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar

PositionType = TypeVar("PositionType")
TransactionType = TypeVar("TransactionType")


@dataclass
class BaseAccount(ABC, Generic[PositionType, TransactionType]):
    initial_cash: float = 0.0
    cash_balance: float = 0.0
    target_allocations: Dict[str, float] = field(default_factory=dict)
    allocation_history: List[Dict[str, Any]] = field(default_factory=list)
    last_rebalance: Optional[str] = None

    def record_allocation(self):
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "total_value": self.get_total_value(),
            "allocations": self.get_allocations(),
        }
        self.allocation_history.append(snapshot)

    def get_total_value(self) -> float:
        return self.cash_balance + self.get_positions_value()

    def get_positions_value(self) -> float:
        return sum(self._get_position_value(ticker) for ticker in self.get_positions())

    def get_allocations(self) -> Dict[str, float]:
        total_value = self.get_total_value()
        if total_value == 0:
            return {}

        allocations = {
            ticker: self._get_position_value(ticker) / total_value
            for ticker in self.get_positions()
        }
        allocations["CASH"] = self.cash_balance / total_value
        return allocations

    def get_breakdown(self) -> Dict[str, Any]:
        total_value = self.get_total_value()
        positions_value = self.get_positions_value()
        return {
            "total_value": total_value,
            "cash_value": self.cash_balance,
            "positions_value": positions_value,
            "current_allocations": self.get_allocations(),
            "target_allocations": self.target_allocations.copy(),
        }

    def get_account_data(self) -> Dict[str, Any]:
        breakdown = self.get_breakdown()
        active_positions = self.get_positions()
        # Convert Position objects to JSON-serializable dicts
        serializable_positions = {}
        for ticker, position in active_positions.items():
            if hasattr(position, "__dict__"):
                serializable_positions[ticker] = position.__dict__
            else:
                serializable_positions[ticker] = position

        return {
            "cash_balance": self.cash_balance,
            "total_value": breakdown["total_value"],
            "pnl": breakdown["total_value"]
            - 1000,  # Simplified PnL against a common baseline
            "positions": serializable_positions,
            "total_positions": len(active_positions),
            "target_allocations": breakdown["target_allocations"],
            "current_allocations": breakdown["current_allocations"],
        }

    @abstractmethod
    def apply_allocation(
        self,
        target_allocations: Dict[str, float],
        price_map: Optional[Dict[str, float]] = None,
    ):
        ...

    @abstractmethod
    def _get_position_value(self, ticker: str) -> float:
        ...

    @abstractmethod
    def get_positions(self) -> Dict[str, Any]:
        ...

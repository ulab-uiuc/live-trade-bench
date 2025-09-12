"""
Base account management system - Abstract base for all account types
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar

PositionType = TypeVar("PositionType")
TransactionType = TypeVar("TransactionType")


@dataclass
class Position:
    symbol: str
    quantity: float
    average_price: float
    current_price: float
    url: Optional[str] = None

    @property
    def market_value(self) -> float:
        return self.quantity * self.current_price

    @property
    def unrealized_pnl(self) -> float:
        return self.quantity * (self.current_price - self.average_price)


@dataclass
class Transaction:
    transaction_id: uuid.UUID
    ticker: str
    quantity: float
    price: float
    transaction_type: str
    timestamp: datetime


@dataclass
class BaseAccount(ABC, Generic[PositionType, TransactionType]):
    """Abstract base class for all trading accounts."""

    initial_cash: float = 0.0
    cash_balance: float = 0.0
    target_allocations: Dict[str, float] = field(default_factory=dict)
    allocation_history: List[Dict[str, Any]] = field(default_factory=list)
    last_rebalance: Optional[str] = None

    def record_allocation(
        self, metadata_map: Optional[Dict[str, Dict[str, Any]]] = None
    ):
        total_value = self.get_total_value()
        profit = total_value - self.initial_cash
        performance = (profit / self.initial_cash) * 100 if self.initial_cash > 0 else 0

        # Create allocation array format with URL information for frontend compatibility
        allocations_array = []
        for asset, allocation in self.target_allocations.items():
            asset_info = {"name": asset, "allocation": allocation}

            # Add URL if available in metadata
            if metadata_map and asset in metadata_map:
                url = metadata_map[asset].get("url")
                if url:
                    asset_info["url"] = url
                question = metadata_map[asset].get("question")
                if question:
                    asset_info["question"] = question

            allocations_array.append(asset_info)

        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "total_value": total_value,
            "profit": profit,
            "performance": performance,
            "allocations": self.target_allocations,  # Keep original format for compatibility
            "allocations_array": allocations_array,  # New format for frontend
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
        total_value = breakdown.get("total_value", self.initial_cash)
        profit = total_value - self.initial_cash
        performance = (profit / self.initial_cash) * 100 if self.initial_cash > 0 else 0

        # Create a serializable portfolio object
        portfolio_details = {
            "cash": self.cash_balance,
            "total_value": total_value,
            "positions": self.get_positions(),
            "target_allocations": breakdown.get("target_allocations", {}),
            "current_allocations": breakdown.get("current_allocations", {}),
        }

        return {
            "profit": profit,
            "performance": performance,
            "portfolio": portfolio_details,
            "allocation_history": self.allocation_history,
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

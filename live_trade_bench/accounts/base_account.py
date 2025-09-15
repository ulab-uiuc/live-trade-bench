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
    initial_cash: float = 0.0
    cash_balance: float = 0.0
    target_allocations: Dict[str, float] = field(default_factory=dict)
    allocation_history: List[Dict[str, Any]] = field(default_factory=list)
    last_rebalance: Optional[str] = None

    def record_allocation(
        self,
        metadata_map: Optional[Dict[str, Dict[str, Any]]] = None,
        backtest_date: Optional[str] = None,
        llm_input: Optional[Dict[str, Any]] = None,
        llm_output: Optional[Dict[str, Any]] = None,
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

        # Use backtest date if provided, otherwise use current time
        if backtest_date:
            # Parse the date and use it as the timestamp (keeping only date part, not time)
            try:
                backtest_datetime = datetime.strptime(backtest_date, "%Y-%m-%d")
                timestamp = backtest_datetime.isoformat()
            except ValueError:
                # Fallback to current time if date parsing fails
                timestamp = datetime.now().isoformat()
        else:
            timestamp = datetime.now().isoformat()

        snapshot = {
            "timestamp": timestamp,
            "total_value": total_value,
            "profit": profit,
            "performance": performance,
            "allocations": self.target_allocations,  # Keep original format for compatibility
            "allocations_array": allocations_array,  # New format for frontend
            "llm_input": llm_input,
            "llm_output": llm_output,
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
            "positions": self.serialize_positions(),
            "target_allocations": breakdown.get("target_allocations", {}),
            "current_allocations": breakdown.get("current_allocations", {}),
        }

        base_data = {
            "profit": profit,
            "performance": performance,
            "portfolio": portfolio_details,
            "allocation_history": self.allocation_history,
            "market_type": self.get_market_type(),
        }

        # Allow subclasses to add additional fields
        base_data.update(self.get_additional_account_data())
        return base_data

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

    @abstractmethod
    def get_market_type(self) -> str:
        """Return the market type identifier (e.g., 'stock', 'polymarket')"""
        ...

    @abstractmethod
    def serialize_positions(self) -> Dict[str, Any]:
        """Serialize positions for API response in market-specific format"""
        ...

    def get_additional_account_data(self) -> Dict[str, Any]:
        """Override in subclasses to add market-specific account data"""
        return {}

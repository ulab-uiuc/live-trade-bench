"""
BitMEX account management system for perpetual contracts trading.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base_account import BaseAccount, Position, Transaction

logger = logging.getLogger(__name__)


@dataclass
class BitMEXAccount(BaseAccount[Position, Transaction]):
    """Account for managing BitMEX perpetual contract positions."""

    positions: Dict[str, Position] = field(default_factory=dict)
    transactions: List[Transaction] = field(default_factory=list)
    total_fees: float = 0.0
    total_funding_fees: float = 0.0  # Track cumulative funding rate payments

    def get_positions(self) -> Dict[str, Position]:
        """Get all active positions with quantity > 0.01."""
        return {
            symbol: pos for symbol, pos in self.positions.items() if pos.quantity > 0.01
        }

    def get_position(self, symbol: str) -> Optional[Position]:
        """Get a specific position by symbol."""
        return self.positions.get(symbol)

    def _get_position_value(self, symbol: str) -> float:
        """Calculate the current market value of a position."""
        position = self.positions.get(symbol)
        return position.market_value if position else 0.0

    def update_position_price(self, symbol: str, current_price: float) -> None:
        """Update the current price of a position."""
        if symbol in self.positions:
            self.positions[symbol].current_price = current_price

    def apply_allocation(
        self,
        target_allocations: Dict[str, float],
        price_map: Optional[Dict[str, float]] = None,
        metadata_map: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> None:
        """
        Apply target allocation by rebalancing positions.

        For BitMEX perpetual contracts, this calculates contract quantities
        based on notional value targets.

        Args:
            target_allocations: Dict mapping symbol to allocation ratio (0-1)
            price_map: Dict mapping symbol to current price
            metadata_map: Dict with additional data (url, funding_rate, etc.)
        """
        if not price_map:
            price_map = {
                symbol: pos.current_price for symbol, pos in self.positions.items()
            }

        # Update positions with latest prices
        for symbol, pos in self.positions.items():
            if symbol in price_map:
                pos.current_price = price_map[symbol]

        # Liquidate portfolio and rebuild
        total_value = self.get_total_value()
        self.cash_balance = total_value
        self.positions.clear()

        for symbol, target_ratio in target_allocations.items():
            if symbol == "CASH" or target_ratio <= 0:
                continue

            price = price_map.get(symbol)
            if price is None or price <= 0:
                continue

            # Calculate target notional value and contract quantity
            target_value = total_value * target_ratio
            quantity = target_value / price

            # Get metadata (url, funding_rate, etc.)
            url = metadata_map.get(symbol, {}).get("url") if metadata_map else None

            self.positions[symbol] = Position(
                symbol=symbol,
                quantity=quantity,
                average_price=price,
                current_price=price,
                url=url,
            )
            self.cash_balance -= target_value

        self.last_rebalance = datetime.now().isoformat()

    def get_market_type(self) -> str:
        """Return market type identifier."""
        return "bitmex"

    def serialize_positions(self) -> Dict[str, Any]:
        """Convert positions to JSON-serializable format."""
        serialized_positions = {}
        for symbol, position in self.positions.items():
            pos_dict = {
                "symbol": position.symbol,
                "quantity": position.quantity,
                "average_price": position.average_price,
                "current_price": position.current_price,
            }
            if position.url:
                pos_dict["url"] = position.url
            serialized_positions[symbol] = pos_dict
        return serialized_positions

    def get_additional_account_data(self) -> Dict[str, Any]:
        """Get BitMEX-specific account data including funding fees."""
        return {
            "total_fees": self.total_fees,
            "total_funding_fees": self.total_funding_fees,
        }

    def _update_market_data(self) -> None:
        """Update market data (placeholder for future enhancements)."""
        pass


def create_bitmex_account(initial_cash: float = 10000.0) -> BitMEXAccount:
    """
    Create a new BitMEX trading account.

    Args:
        initial_cash: Starting capital (default $10,000)

    Returns:
        Initialized BitMEXAccount instance
    """
    return BitMEXAccount(initial_cash=initial_cash, cash_balance=initial_cash)

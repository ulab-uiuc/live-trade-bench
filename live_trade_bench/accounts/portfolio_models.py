"""
Simplified portfolio management data models
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class PortfolioSummary:
    """High-level portfolio summary."""

    agent_name: str
    total_value: float
    cash_balance: float
    position_count: int
    needs_rebalancing: bool
    last_rebalance: str = None
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

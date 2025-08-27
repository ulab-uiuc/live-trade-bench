"""
Simplified portfolio management data models
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional


@dataclass
class PortfolioTarget:
    """Portfolio allocation target for an asset."""
    ticker: str
    target_allocation: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    reasoning: str
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        
        # Validate allocation
        if not (0.0 <= self.target_allocation <= 1.0):
            raise ValueError(f"Invalid allocation: {self.target_allocation} (must be 0.0-1.0)")
        
        # Validate confidence
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"Invalid confidence: {self.confidence} (must be 0.0-1.0)")


@dataclass
class AllocationChange:
    """Record of a portfolio allocation change."""
    ticker: str
    old_ratio: float
    new_ratio: float
    timestamp: str
    reason: str
    confidence: float
    agent_name: str


@dataclass
class PortfolioStatus:
    """Current portfolio status and allocation information."""
    total_value: float
    cash_balance: float
    positions: Dict[str, Dict[str, Any]]
    current_allocations: Dict[str, float]
    target_allocations: Dict[str, float]
    needs_rebalancing: bool
    last_rebalance: Optional[str]
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


@dataclass
class RebalanceAction:
    """Action needed to rebalance portfolio."""
    ticker: str
    current_ratio: float
    target_ratio: float
    value_adjustment: float
    action: str  # "buy" or "sell"
    quantity: Optional[float] = None
    estimated_cost: Optional[float] = None


@dataclass
class RebalancePlan:
    """Complete portfolio rebalancing plan."""
    status: str  # "no_rebalancing_needed" or "rebalancing_required"
    actions: list[RebalanceAction]
    timestamp: str
    total_adjustment_value: float = 0.0
    
    def __post_init__(self):
        if self.actions:
            self.total_adjustment_value = sum(
                abs(action.value_adjustment) for action in self.actions
            )


@dataclass
class PortfolioSummary:
    """High-level portfolio summary."""
    agent_name: str
    total_value: float
    cash_balance: float
    position_count: int
    needs_rebalancing: bool
    last_rebalance: Optional[str]
    performance: Dict[str, float]  # return, return_pct, etc.
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

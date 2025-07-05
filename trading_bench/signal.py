from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Signal:
    entry_time: datetime
    entry_price: float
    eval_time: datetime


@dataclass
class TradeRecord:
    """Complete trade record with all trading information"""
    entry_time: datetime
    entry_price: float
    exit_time: datetime
    exit_price: float
    return_pct: float  # Return percentage
    trade_duration: int  # Trading duration in days
    volume: Optional[int] = None  # Trading volume (if available)
    high_during_trade: Optional[float] = None  # Highest price during trade
    low_during_trade: Optional[float] = None   # Lowest price during trade


@dataclass
class ReturnRecord:
    entry_time: datetime
    exit_time: datetime
    return_pct: float

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Signal:
    entry_time: datetime
    entry_price: float
    eval_time: datetime
    ticker: str = "AAPL"
    quantity: int = 1


@dataclass
class TradeRecord:
    """Complete trade record with all trading information"""

    entry_time: datetime
    entry_price: float
    exit_time: datetime
    exit_price: float
    return_pct: float  # Return percentage
    trade_duration: int  # Trading duration in days
    volume: int | None = None  # Trading volume (if available)
    high_during_trade: float | None = None  # Highest price during trade
    low_during_trade: float | None = None  # Lowest price during trade


@dataclass
class ReturnRecord:
    entry_time: datetime
    exit_time: datetime
    return_pct: float

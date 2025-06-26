from dataclasses import dataclass
from datetime import datetime


@dataclass
class Signal:
    entry_time: datetime
    entry_price: float
    eval_time: datetime


@dataclass
class ReturnRecord:
    entry_time: datetime
    exit_time: datetime
    return_pct: float

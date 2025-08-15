from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class ModelStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    TRAINING = "training"


class ModelCategory(str, Enum):
    STOCK = "stock"
    POLYMARKET = "polymarket"


class TradeType(str, Enum):
    BUY = "buy"
    SELL = "sell"


class ActionType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class ActionStatus(str, Enum):
    PENDING = "pending"
    EXECUTED = "executed"
    EVALUATED = "evaluated"


class NewsImpact(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class NewsCategory(str, Enum):
    MARKET = "market"
    ECONOMIC = "economic"
    COMPANY = "company"
    TECH = "tech"


class TradingModel(BaseModel):
    id: str
    name: str
    category: ModelCategory
    performance: float
    accuracy: float
    trades: int
    profit: float
    status: ModelStatus
    total_value: float | None = None
    cash_balance: float | None = None
    active_positions: int | None = None
    is_activated: bool | None = None
    recent_performance: dict | None = None
    llm_available: bool | None = None
    market_type: str | None = None


class TradingModelCreate(BaseModel):
    name: str
    performance: float
    accuracy: float
    trades: int
    profit: float
    status: ModelStatus


class Trade(BaseModel):
    id: str
    timestamp: datetime
    symbol: str
    type: TradeType
    amount: int
    price: float
    profit: float
    model: str


class TradeCreate(BaseModel):
    symbol: str
    type: TradeType
    amount: int
    price: float
    profit: float
    model: str


class TradingSummary(BaseModel):
    total_profit: float
    total_trades: int
    profitable_trades: int
    win_rate: float
    average_profit: float
    today_profit: float


class NewsItem(BaseModel):
    id: str
    title: str
    summary: str
    source: str
    published_at: datetime
    impact: NewsImpact
    category: NewsCategory
    url: str


class NewsItemCreate(BaseModel):
    title: str
    summary: str
    source: str
    published_at: datetime
    impact: NewsImpact
    category: NewsCategory
    url: str


class Portfolio(BaseModel):
    cash: float
    holdings: dict[str, float]  # ticker -> quantity


class TradingAction(BaseModel):
    id: str
    agent_id: str  # model identifier (e.g., "claude-3.5-sonnet")
    agent_name: str  # human readable name
    agent_type: str = "trading_agent"
    action: ActionType
    description: str
    status: ActionStatus
    timestamp: datetime
    targets: list[str]  # tickers affected
    metadata: dict


class SystemLogStats(BaseModel):
    total_actions: int
    pending_actions: int
    executed_actions: int
    evaluated_actions: int
    models_active: int
    recent_activity: int  # last hour


class APIResponse(BaseModel):
    success: bool
    message: str
    data: dict | None = None

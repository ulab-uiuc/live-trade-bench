from datetime import datetime
from enum import Enum
from typing import Any, Dict

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
    REBALANCE = "REBALANCE"


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
    recent_performance: Dict[str, Any] | None = None
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
    stock_symbol: str | None = None


class NewsItemCreate(BaseModel):
    title: str
    summary: str
    source: str
    published_at: datetime
    impact: NewsImpact
    category: NewsCategory
    url: str
    stock_symbol: str | None = None


class Portfolio(BaseModel):
    cash: float
    holdings: dict[str, float]  # ticker -> quantity


class PortfolioHistoryPoint(BaseModel):
    timestamp: str
    holdings: dict[str, float]
    prices: dict[str, float]
    cash: float
    totalValue: float


class PortfolioData(BaseModel):
    model_id: str
    model_name: str
    category: str
    cash: float
    total_value: float
    return_pct: float
    holdings: dict[str, float]  # ticker/asset -> quantity
    positions: dict[str, Dict[str, Any]]  # detailed position info
    # Target allocations proposed by the agent (e.g., {"AAPL": 0.15, ... , "CASH": 0.1})
    target_allocations: dict[str, float] | None = None
    unrealized_pnl: float
    market_data_available: bool
    last_updated: str
    # Real-time data fields
    total_value_realtime: float | None = None
    return_pct_realtime: float | None = None
    unrealized_pnl_realtime: float | None = None
    # Portfolio history for area chart
    portfolio_history: list[PortfolioHistoryPoint] | None = None


class PortfolioAllocation(BaseModel):
    asset: str
    target_allocation: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    reasoning: str


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
    metadata: Dict[str, Any]


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
    data: Dict[str, Any] | None = None

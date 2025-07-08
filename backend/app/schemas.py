from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class ModelStatus(str, Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    TRAINING = 'training'


class TradeType(str, Enum):
    BUY = 'buy'
    SELL = 'sell'


class NewsImpact(str, Enum):
    HIGH = 'high'
    MEDIUM = 'medium'
    LOW = 'low'


class NewsCategory(str, Enum):
    MARKET = 'market'
    ECONOMIC = 'economic'
    COMPANY = 'company'
    TECH = 'tech'


class TradingModel(BaseModel):
    id: str
    name: str
    performance: float
    accuracy: float
    trades: int
    profit: float
    status: ModelStatus


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


class APIResponse(BaseModel):
    success: bool
    message: str
    data: dict | None = None

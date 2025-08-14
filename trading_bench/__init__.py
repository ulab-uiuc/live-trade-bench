"""
Trading Bench - AI Trading Simulation Package
"""

from .accounts import (
    BaseAccount,
    PolymarketAccount,
    PolymarketAction,
    PolymarketPosition,
    PolymarketTransaction,
    StockAccount,
    StockAction,
    StockPosition,
    StockTransaction,
    create_polymarket_account,
    create_stock_account,
    eval_account,
    eval_polymarket_account,
)
from .agents import (
    AIPolymarketAgent,
    AITradingAgent,
    PolymarketTradingSystem,
    TradingSystem,
    create_polymarket_agent,
    create_polymarket_trading_system,
    create_trading_system,
)

__all__ = [
    # Base classes
    "BaseAccount",
    # Stock trading
    "AITradingAgent",
    "TradingSystem",
    "create_trading_system",
    "StockAccount",
    "StockPosition",
    "StockTransaction",
    "StockAction",
    "create_stock_account",
    "eval_account",
    # Prediction market trading
    "AIPolymarketAgent",
    "PolymarketTradingSystem",
    "create_polymarket_agent",
    "create_polymarket_trading_system",
    "PolymarketAccount",
    "PolymarketPosition",
    "PolymarketTransaction",
    "PolymarketAction",
    "create_polymarket_account",
    "eval_polymarket_account",
]

__version__ = "1.0.0"

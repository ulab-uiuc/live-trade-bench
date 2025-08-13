"""
Trading Bench - AI Trading Simulation Package
"""

from .agents import (
    AITradingAgent, TradingSystem, create_trading_system,
    AIPolymarketAgent, PolymarketTradingSystem, 
    create_polymarket_agent, create_polymarket_trading_system
)
from .evaluators import (
    BaseAccount,
    StockAccount, StockPosition, StockTransaction, StockAction,
    PolymarketAccount, PolymarketPosition, PolymarketTransaction, PolymarketAction,
    create_stock_account, create_polymarket_account,
    eval_account, eval_polymarket_account,
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

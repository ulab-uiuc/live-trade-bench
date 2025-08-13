"""
Trading Bench Agents Package
"""

from .polymarket_agent import (
    AIPolymarketAgent,
    PolymarketTradingSystem,
    create_polymarket_agent,
    create_polymarket_trading_system,
)
from .stock_agent import AITradingAgent, TradingSystem, create_trading_system

__all__ = [
    # Stock trading agents
    "AITradingAgent",
    "TradingSystem",
    "create_trading_system",
    # Prediction market agents
    "AIPolymarketAgent",
    "PolymarketTradingSystem",
    "create_polymarket_agent",
    "create_polymarket_trading_system",
]

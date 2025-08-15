"""
Trading Bench - A comprehensive trading simulation framework

This package provides tools for:
- Multi-asset trading simulation (stocks, prediction markets)
- AI-powered trading agents using LLMs
- Real-time data fetching from various sources
- Portfolio management and performance tracking
"""

# Import core components
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
)
from .agents import (
    BaseAgent,
    LLMPolyMarketAgent,
    LLMStockAgent,
    PolymarketTradingSystem,
    StockTradingSystem,
    create_polymarket_agent,
    create_polymarket_trading_system,
    create_stock_agent,
    create_stock_trading_system,
)
from .fetchers import (
    BaseFetcher,
    NewsFetcher,
    PolymarketFetcher,
    fetch_current_market_price,
    fetch_current_stock_price,
    fetch_trending_markets,
    fetch_trending_stocks,
)
from .utils import call_llm, parse_trading_response

# Define what gets exported when importing *
__all__ = [
    # Accounts
    "BaseAccount",
    "StockAccount",
    "StockPosition",
    "StockTransaction",
    "StockAction",
    "create_stock_account",
    "PolymarketAccount",
    "PolymarketPosition",
    "PolymarketTransaction",
    "PolymarketAction",
    "create_polymarket_account",
    # Agents
    "BaseAgent",
    "LLMStockAgent",
    "StockTradingSystem",
    "LLMPolyMarketAgent",
    "PolymarketTradingSystem",
    "create_polymarket_trading_system",
    "create_polymarket_agent",
    "create_stock_agent",
    "create_stock_trading_system",
    # Fetchers
    "BaseFetcher",
    "NewsFetcher",
    "PolymarketFetcher",
    "fetch_trending_markets",
    "fetch_current_market_price",
    "fetch_trending_stocks",
    "fetch_current_stock_price",
    # Utils
    "call_llm",
    "parse_trading_response",
]

__version__ = "1.0.0"

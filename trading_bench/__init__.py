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
    StockAccount, 
    StockPosition, 
    StockTransaction, 
    StockAction,
    create_stock_account,
    PolymarketAccount,
    PolymarketPosition, 
    PolymarketTransaction, 
    PolymarketAction,
    create_polymarket_account
)

from .agents import (
    BaseAgent,
    LLMStockAgent, 
    StockTradingSystem, 
    create_trading_system,
    LLMPolyMarketAgent, 
    PolymarketTradingSystem, 
    create_polymarket_agent, 
    create_polymarket_trading_system
)

from .fetchers import (
    BaseFetcher,
    NewsFetcher,
    PolymarketFetcher,
    fetch_trending_markets,
    fetch_current_market_price,
)

# Optional fetchers (may not be available if dependencies missing)
try:
    from .fetchers import StockFetcher, fetch_trending_stocks, fetch_current_stock_price
except ImportError:
    pass

try:
    from .fetchers import OptionFetcher
except ImportError:
    pass

try:
    from .fetchers import RedditFetcher
except ImportError:
    pass

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
    "create_trading_system",
    "LLMPolyMarketAgent", 
    "PolymarketTradingSystem", 
    "create_polymarket_agent", 
    "create_polymarket_trading_system",
    
    # Fetchers
    "BaseFetcher",
    "NewsFetcher",
    "PolymarketFetcher",
    "fetch_trending_markets",
    "fetch_current_market_price",
    
    # Utils
    "call_llm", 
    "parse_trading_response",
]

__version__ = "1.0.0"

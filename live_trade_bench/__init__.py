"""
Trading Bench - A comprehensive portfolio management framework

This package provides tools for:
- Multi-asset portfolio management (stocks, prediction markets)
- AI-powered portfolio allocation using LLMs
- Real-time data fetching from various sources
- Portfolio management and performance tracking
"""

# Import core components
from .accounts.portfolio_models import (
    PortfolioSummary,
)
from .agents import (
    BaseAgent,
    LLMPolyMarketAgent,
    LLMStockAgent,
    PolymarketPortfolioSystem,
    StockPortfolioSystem,
    create_polymarket_agent,
    create_polymarket_portfolio_system,
    create_stock_agent,
    create_stock_portfolio_system,
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
from .utils import call_llm, parse_portfolio_response, parse_trading_response

# Define what gets exported when importing *
__all__ = [
    # Accounts
    "BaseAccount",
    "StockAccount",
    "StockPosition",
    "StockTransaction",
    "create_stock_account",
    "PolymarketAccount",
    "PolymarketPosition",
    "PolymarketTransaction",
    "create_polymarket_account",
    # Portfolio models
    "PortfolioTarget",
    "AllocationChange",
    "PortfolioStatus",
    "RebalanceAction",
    "RebalancePlan",
    "PortfolioSummary",
    # Agents
    "BaseAgent",
    "LLMStockAgent",
    "StockPortfolioSystem",
    "LLMPolyMarketAgent",
    "PolymarketPortfolioSystem",
    "create_polymarket_portfolio_system",
    "create_polymarket_agent",
    "create_stock_agent",
    "create_stock_portfolio_system",
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
    "parse_portfolio_response",
]

__version__ = "2.0.0"

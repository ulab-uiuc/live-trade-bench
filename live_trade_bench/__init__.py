"""
Trading Bench - A comprehensive portfolio management framework

This package provides tools for:
- Multi-asset portfolio management (stocks, prediction markets)
- AI-powered portfolio allocation using LLMs
- Real-time data fetching from various sources
- Portfolio management and performance tracking
"""

from __future__ import annotations

# Accounts
from .accounts import (
    BaseAccount,
    PolymarketAccount,
    Position,
    StockAccount,
    Transaction,
    create_polymarket_account,
    create_stock_account,
)

# Agents
from .agents.base_agent import BaseAgent
from .agents.polymarket_agent import LLMPolyMarketAgent
from .agents.stock_agent import LLMStockAgent

# backtest
from .backtest.backtest_runner import BacktestRunner

# Fetchers
from .fetchers.base_fetcher import BaseFetcher
from .fetchers.news_fetcher import NewsFetcher, fetch_news_data
from .fetchers.option_fetcher import OptionFetcher
from .fetchers.polymarket_fetcher import (
    PolymarketFetcher,
    fetch_current_market_price,
    fetch_market_price_on_date,
    fetch_token_price,
    fetch_trending_markets,
)
from .fetchers.reddit_fetcher import RedditFetcher
from .fetchers.stock_fetcher import StockFetcher, fetch_stock_price

# Core Systems
from .systems.polymarket_system import (
    PolymarketPortfolioSystem,
    create_polymarket_portfolio_system,
)
from .systems.stock_system import StockPortfolioSystem, create_stock_portfolio_system

# Utilities
from .utils.llm_client import call_llm
from .utils.logger import setup_logger

__all__ = [
    # Systems
    "StockPortfolioSystem",
    "create_stock_portfolio_system",
    "PolymarketPortfolioSystem",
    "create_polymarket_portfolio_system",
    # Accounts
    "BaseAccount",
    "Position",
    "Transaction",
    "StockAccount",
    "create_stock_account",
    "PolymarketAccount",
    "create_polymarket_account",
    # Agents
    "BaseAgent",
    "LLMStockAgent",
    "LLMPolyMarketAgent",
    # Fetchers
    "BaseFetcher",
    "StockFetcher",
    "fetch_stock_price",
    "NewsFetcher",
    "fetch_news_data",
    "OptionFetcher",
    "PolymarketFetcher",
    "fetch_trending_markets",
    "fetch_current_market_price",
    "fetch_market_price_on_date",
    "fetch_token_price",
    "RedditFetcher",
    # backtest
    "BacktestRunner",
    # Utilities
    "call_llm",
    "setup_logger",
]

__version__ = "2.0.0"

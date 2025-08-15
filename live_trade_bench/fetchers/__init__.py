"""
Fetchers Package - Data fetching utilities for various financial markets
"""

from .base_fetcher import BaseFetcher
from .news_fetcher import NewsFetcher
from .polymarket_fetcher import (
    PolymarketFetcher,
    fetch_current_market_price,
    fetch_trending_markets,
)

# Optional imports with graceful degradation
try:
    from .option_fetcher import OptionFetcher
except ImportError:
    OptionFetcher = None

try:
    from .stock_fetcher import (
        StockFetcher,
        fetch_current_stock_price,
        fetch_trending_stocks,
    )
except ImportError:
    StockFetcher = None
    fetch_trending_stocks = None
    fetch_current_stock_price = None

try:
    from .reddit_fetcher import RedditFetcher
except ImportError:
    RedditFetcher = None

# Export only the classes and main functions that are actually used
__all__ = [
    "BaseFetcher",
    "NewsFetcher",
    "PolymarketFetcher",
    "fetch_trending_markets",
    "fetch_current_market_price",
]

# Add optional exports only if they're available
if OptionFetcher is not None:
    __all__.append("OptionFetcher")

if StockFetcher is not None:
    __all__.extend(
        ["StockFetcher", "fetch_trending_stocks", "fetch_current_stock_price"]
    )

if RedditFetcher is not None:
    __all__.append("RedditFetcher")

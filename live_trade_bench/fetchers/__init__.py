"""
Fetchers Package - Data fetching utilities for various financial markets
"""

from typing import TYPE_CHECKING

from .base_fetcher import BaseFetcher
from .bitmex_fetcher import BitMEXFetcher
from .news_fetcher import NewsFetcher
from .polymarket_fetcher import PolymarketFetcher, fetch_trending_markets

if TYPE_CHECKING:
    # Optional imports for type checking only
    from .option_fetcher import OptionFetcher
    from .reddit_fetcher import RedditFetcher
    from .stock_fetcher import (
        StockFetcher,
        fetch_current_stock_price,
        fetch_trending_stocks,
    )
else:
    # Runtime imports - try but degrade gracefully
    try:
        from .option_fetcher import OptionFetcher  # type: ignore
    except Exception:
        OptionFetcher = None  # type: ignore

    try:
        from .stock_fetcher import (
            StockFetcher,
            fetch_current_stock_price,
            fetch_trending_stocks,
        )
    except Exception:
        StockFetcher = None  # type: ignore
        fetch_trending_stocks = None  # type: ignore
        fetch_current_stock_price = None  # type: ignore

    try:
        from .reddit_fetcher import RedditFetcher  # type: ignore
    except Exception:
        RedditFetcher = None  # type: ignore


# Export only the classes and main functions that are actually used
__all__ = [
    "BaseFetcher",
    "BitMEXFetcher",
    "NewsFetcher",
    "PolymarketFetcher",
    "fetch_trending_markets",
]

if OptionFetcher is not None:
    __all__.append("OptionFetcher")

if StockFetcher is not None:
    __all__.extend(
        ["StockFetcher", "fetch_trending_stocks", "fetch_current_stock_price"]
    )

if RedditFetcher is not None:
    __all__.append("RedditFetcher")

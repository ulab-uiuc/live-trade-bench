"""
Stock data fetcher for trading bench.

This module provides:
1. StockFetcher class - Core fetcher class with methods
2. fetch_trending_stocks() - Standalone function using the class
3. fetch_current_stock_price() - Standalone function using the class
"""

from typing import Dict, List, Optional

import yfinance as yf

from trading_bench.fetchers.base_fetcher import BaseFetcher


class StockFetcher(BaseFetcher):
    """Fetcher for stock price data from Yahoo Finance."""

    def __init__(self, min_delay: float = 1.0, max_delay: float = 3.0):
        """Initialize the stock fetcher."""
        super().__init__(min_delay, max_delay)

    def fetch(self, mode: str, **kwargs):
        """
        Unified fetch interface for StockFetcher.

        Args:
            mode: The type of data to fetch ('trending_stocks' or 'stock_price')
            **kwargs: Arguments for the specific fetch method
        """
        if mode == "trending_stocks":
            return self.get_trending_stocks(limit=kwargs.get("limit", 10))
        elif mode == "stock_price":
            if "ticker" not in kwargs:
                raise ValueError("ticker is required for stock_price")
            return self.get_current_stock_price(kwargs["ticker"])
        else:
            raise ValueError(f"Unknown fetch mode: {mode}")

    def get_trending_stocks(self, limit: int = 10) -> List[Dict]:
        """
        Get trending/popular stock tickers.

        Args:
            limit: Maximum number of stocks to return

        Returns:
            List of dictionaries containing stock basic info
        """
        # Popular stocks for demo purposes
        trending_stocks = [
            {"ticker": "AAPL", "name": "Apple Inc.", "sector": "Technology"},
            {"ticker": "MSFT", "name": "Microsoft Corporation", "sector": "Technology"},
            {"ticker": "GOOGL", "name": "Alphabet Inc.", "sector": "Technology"},
            {
                "ticker": "AMZN",
                "name": "Amazon.com Inc.",
                "sector": "Consumer Discretionary",
            },
            {
                "ticker": "TSLA",
                "name": "Tesla Inc.",
                "sector": "Consumer Discretionary",
            },
            {"ticker": "META", "name": "Meta Platforms Inc.", "sector": "Technology"},
            {"ticker": "NVDA", "name": "NVIDIA Corporation", "sector": "Technology"},
            {
                "ticker": "JPM",
                "name": "JPMorgan Chase & Co.",
                "sector": "Financial Services",
            },
            {"ticker": "JNJ", "name": "Johnson & Johnson", "sector": "Healthcare"},
            {"ticker": "V", "name": "Visa Inc.", "sector": "Financial Services"},
            {
                "ticker": "PG",
                "name": "Procter & Gamble Co.",
                "sector": "Consumer Staples",
            },
            {
                "ticker": "UNH",
                "name": "UnitedHealth Group Inc.",
                "sector": "Healthcare",
            },
        ]

        return trending_stocks[:limit]

    def get_current_stock_price(self, ticker: str) -> Optional[float]:
        """
        Get current stock price for a specific ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Current stock price or None if failed
        """
        return self.get_current_price(ticker)

    def _download_price_data(
        self, ticker: str, start_date: str, end_date: str, interval: str
    ):
        """
        Internal function to download price data with error handling.
        Args:
            ticker:     Stock ticker symbol.
            start_date: YYYY-MM-DD
            end_date:   YYYY-MM-DD
            interval:   yfinance interval string
        Returns:
            pandas.DataFrame: Downloaded price data
        """
        df = yf.download(
            tickers=ticker,
            start=start_date,
            end=end_date,
            interval=interval,
            progress=False,
            auto_adjust=True,
            prepost=True,  # Include pre and post market data
            threads=True,  # Use threading for faster downloads
        )

        if df.empty:
            raise RuntimeError(
                f"No data returned for {ticker} {start_date}→{end_date} @ {interval}"
            )

        return df

    def get_current_price(self, ticker: str) -> Optional[float]:
        """
        Get the current stock price for a given ticker.
        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL', 'GOOGL').
        Returns:
            float: Current stock price, or None if unable to fetch.
        """
        try:
            stock = yf.Ticker(ticker)

            # Strategy 1: Try fast_info (fastest)
            try:
                fast_info = stock.fast_info
                if hasattr(fast_info, "last_price") and fast_info.last_price:
                    price = float(fast_info.last_price)
                    if price > 0:
                        return price
            except Exception:
                pass

            # Strategy 2: Try info (more comprehensive)
            try:
                info = stock.info
                price_fields = ["currentPrice", "regularMarketPrice", "previousClose"]
                for field in price_fields:
                    if field in info and info[field]:
                        price = float(info[field])
                        if price > 0:
                            return price
            except Exception:
                pass

            # Strategy 3: Try 1-day history (reliable but slower)
            try:
                history = stock.history(period="1d", interval="1m")
                if not history.empty:
                    # Get the latest close price
                    latest_price = history["Close"].iloc[-1]
                    if latest_price and latest_price > 0:
                        return float(latest_price)
            except Exception:
                pass

            # Strategy 4: Last resort - basic download
            try:
                data = yf.download(ticker, period="1d", interval="1m", progress=False)
                if not data.empty:
                    latest_price = data["Close"].iloc[-1]
                    return float(latest_price)
            except Exception:
                pass

            print(f"⚠️ Could not fetch price for {ticker}")
            return None

        except Exception as e:
            print(f"⚠️ Error fetching price for {ticker}: {e}")
            return None

    def fetch_stock_data(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
        interval: str = "1d",
    ):
        """
        Fetch historical stock data from Yahoo Finance.
        Args:
            ticker:     Stock ticker symbol.
            start_date: Start date in YYYY-MM-DD format.
            end_date:   End date in YYYY-MM-DD format.
            interval:   Data interval ('1d', '1h', '5m', etc.).
        Returns:
            pandas.DataFrame: Historical stock price data.
        """
        try:
            self._rate_limit_delay()  # Rate limiting
            df = self._download_price_data(ticker, start_date, end_date, interval)
            return df
        except Exception as e:
            print(f"Error fetching stock data for {ticker}: {e}")
            raise


# Standalone functions that use the class
def fetch_trending_stocks(limit: int = 10) -> List[Dict]:
    """
    Fetch trending/popular stocks.

    Args:
        limit: Maximum number of stocks to return (default: 10)

    Returns:
        List of dictionaries containing stock basic info
    """
    fetcher = StockFetcher()
    stocks = fetcher.get_trending_stocks(limit=limit)
    print(f"📊 Fetched {len(stocks)} trending stocks")
    return stocks


def fetch_current_stock_price(ticker: str) -> Optional[float]:
    """
    Fetch current price for a specific stock ticker.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Current stock price or None if failed
    """
    fetcher = StockFetcher()
    return fetcher.get_current_stock_price(ticker)

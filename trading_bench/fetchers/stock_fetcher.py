"""
Stock data fetcher for trading bench.

This module provides functions to fetch stock price data from Yahoo Finance
using yfinance library.
"""

import yfinance as yf
from datetime import datetime, timedelta
from typing import Optional

from trading_bench.fetchers.base_fetcher import BaseFetcher


class StockFetcher(BaseFetcher):
    """Fetcher for stock price data from Yahoo Finance."""

    def __init__(self, min_delay: float = 1.0, max_delay: float = 3.0):
        """Initialize the stock fetcher."""
        super().__init__(min_delay, max_delay)

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
        Get current/latest price for a ticker using multiple methods
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Current price or None if failed
        """
        try:
            # Method 1: Use Ticker.info for real-time price
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Try different price fields
            price_fields = ['currentPrice', 'regularMarketPrice', 'previousClose', 'open']
            for field in price_fields:
                price = info.get(field)
                if price and price > 0:
                    return float(price)
                    
        except Exception as e:
            print(f"⚠️ Method 1 failed for {ticker}: {e}")
            
        try:
            # Method 2: Get latest minute data
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1d", interval="1m")
            if not hist.empty:
                latest_price = hist['Close'].iloc[-1]
                if latest_price > 0:
                    return float(latest_price)
                    
        except Exception as e:
            print(f"⚠️ Method 2 failed for {ticker}: {e}")
            
        try:
            # Method 3: Get latest daily data
            stock = yf.Ticker(ticker)
            hist = stock.history(period="5d")
            if not hist.empty:
                latest_price = hist['Close'].iloc[-1]
                if latest_price > 0:
                    return float(latest_price)
                    
        except Exception as e:
            print(f"⚠️ Method 3 failed for {ticker}: {e}")
            
        return None

    def fetch(
        self, ticker: str, start_date: str, end_date: str, resolution: str = "1"
    ) -> dict:
        """
        Fetches historical OHLCV price data for a ticker via yfinance and returns it as formatted JSON.
        Args:
            ticker:     Stock ticker symbol.
            start_date: YYYY-MM-DD
            end_date:   YYYY-MM-DD
            resolution: '1', '5', '15', '30', '60', 'D', 'W', 'M'
        Returns:
            dict: Price data in JSON format with date keys and OHLCV values.
        """
        # map your resolution codes to yfinance intervals
        interval_map = {
            "1": "1m",
            "5": "5m",
            "15": "15m",
            "30": "30m",
            "60": "60m",
            "D": "1d",
            "W": "1wk",
            "M": "1mo",
        }
        interval = interval_map.get(resolution.upper(), "1d")

        # For real-time data, adjust end_date to include today
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        if end_dt.date() <= datetime.now().date():
            # Extend end_date to tomorrow to get today's data
            end_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        # download data with retry logic
        df = self.execute_with_retry(
            self._download_price_data, ticker, start_date, end_date, interval
        )

        # Build date-indexed dict
        data = {}
        for idx, row in df.iterrows():
            # Handle both single ticker and multi-ticker scenarios
            if hasattr(row, 'iloc'):
                # Multi-ticker format
                open_price = float(row["Open"].iloc[0]) if not row["Open"].empty else 0
                high_price = float(row["High"].iloc[0]) if not row["High"].empty else 0
                low_price = float(row["Low"].iloc[0]) if not row["Low"].empty else 0
                close_price = float(row["Close"].iloc[0]) if not row["Close"].empty else 0
                volume = int(row["Volume"].iloc[0]) if not row["Volume"].empty else 0
            else:
                # Single ticker format
                open_price = float(row["Open"]) if row["Open"] > 0 else 0
                high_price = float(row["High"]) if row["High"] > 0 else 0
                low_price = float(row["Low"]) if row["Low"] > 0 else 0
                close_price = float(row["Close"]) if row["Close"] > 0 else 0
                volume = int(row["Volume"]) if row["Volume"] > 0 else 0

            # idx is a pandas.Timestamp
            if interval in ["1m", "5m", "15m", "30m", "60m"]:
                # For intraday data, include time
                date_str = idx.strftime("%Y-%m-%d %H:%M:%S")
            else:
                # For daily+ data, use date only
                date_str = idx.strftime("%Y-%m-%d")
                
            data[date_str] = {
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "close": close_price,
                "volume": volume,
            }

        return data


def fetch_stock_data(
    ticker: str, start_date: str, end_date: str, resolution: str = "D"
) -> dict:
    """
    Fetches historical OHLCV price data for a ticker via yfinance and returns it as formatted JSON.
    Args:
        ticker:     Stock ticker symbol.
        start_date: YYYY-MM-DD
        end_date:   YYYY-MM-DD
        resolution: '1', '5', '15', '30', '60', 'D', 'W', 'M'
    Returns:
        dict: Price data in JSON format with date keys and OHLCV values.
    """
    fetcher = StockFetcher()
    return fetcher.fetch(ticker, start_date, end_date, resolution)


def get_current_stock_price(ticker: str) -> Optional[float]:
    """
    Get current stock price using optimized yfinance methods
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Current price or None if failed
    """
    fetcher = StockFetcher()
    return fetcher.get_current_price(ticker)

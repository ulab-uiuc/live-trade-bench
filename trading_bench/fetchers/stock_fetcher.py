"""
Stock data fetcher for trading bench.

This module provides functions to fetch stock price data from Yahoo Finance
using yfinance library.
"""

import random
import time
from typing import Dict

import yfinance as yf

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
        )

        if df.empty:
            raise RuntimeError(
                f'No data returned for {ticker} {start_date}→{end_date} @ {interval}'
            )

        return df

    def fetch(
        self, ticker: str, start_date: str, end_date: str, resolution: str = 'D'
    ) -> Dict:
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
            '1': '1m',
            '5': '5m',
            '15': '15m',
            '30': '30m',
            '60': '60m',
            'D': '1d',
            'W': '1wk',
            'M': '1mo',
        }
        interval = interval_map.get(resolution.upper(), '1d')

        # download data with retry logic
        df = self.execute_with_retry(
            self._download_price_data, ticker, start_date, end_date, interval
        )

        # Build date-indexed dict
        data = {}
        for idx, row in df.iterrows():
            # idx is a pandas.Timestamp
            date_str = idx.strftime('%Y-%m-%d')
            data[date_str] = {
                'open': float(row['Open'].iloc[0]),
                'high': float(row['High'].iloc[0]),
                'low': float(row['Low'].iloc[0]),
                'close': float(row['Close'].iloc[0]),
                'volume': int(row['Volume'].iloc[0]),
            }

        return data


# Backward compatibility functions
def fetch_price_data(
    ticker: str, start_date: str, end_date: str, resolution: str = 'D'
) -> Dict:
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

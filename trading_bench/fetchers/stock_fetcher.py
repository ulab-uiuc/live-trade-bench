"""
Stock data fetcher for trading bench.

This module provides functions to fetch stock price data from Yahoo Finance
using yfinance library.
"""

import random
import time

import yfinance as yf
from tenacity import (retry, retry_if_exception_type, stop_after_attempt,
                      wait_exponential)


def _download_price_data(ticker: str, start_date: str, end_date: str, interval: str):
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
    # Random delay before each request to avoid rate limiting
    time.sleep(random.uniform(1, 3))

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


@retry(
    retry=retry_if_exception_type((RuntimeError, Exception)),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    stop=stop_after_attempt(3),
)
def fetch_price_data(
    ticker: str, start_date: str, end_date: str, resolution: str = 'D'
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
    df = _download_price_data(ticker, start_date, end_date, interval)

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

    # be polite with any rate limits
    time.sleep(1)

    # Return the price data as JSON
    return data

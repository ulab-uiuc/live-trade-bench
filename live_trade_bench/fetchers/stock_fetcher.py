"""
Stock data fetcher for trading bench.

This module provides:
1. StockFetcher class - Core fetcher class with methods
2. fetch_trending_stocks() - Standalone function using the class
3. fetch_current_stock_price() - Standalone function using the class
"""

from typing import Dict, List, Optional

import yfinance as yf

from live_trade_bench.fetchers.base_fetcher import BaseFetcher


class StockFetcher(BaseFetcher):
    def __init__(self, min_delay: float = 1.0, max_delay: float = 3.0):
        """Initialize the stock fetcher."""
        super().__init__(min_delay, max_delay)

    def fetch(self, mode: str, **kwargs):
        if mode == "trending_stocks":
            return self.get_trending_stocks(limit=kwargs.get("limit", 10))
        elif mode == "stock_price":
            if "ticker" not in kwargs:
                raise ValueError("ticker is required for stock_price")
            return self.get_current_stock_price(kwargs["ticker"])
        else:
            raise ValueError(f"Unknown fetch mode: {mode}")

    def get_trending_stocks(self, limit: int = 10) -> List[Dict]:
        trending_tickers = [
            "AAPL",
            "MSFT",
            "GOOGL",
            "AMZN",
            "TSLA",
            "META",
            "NVDA",
            "JPM",
            "JNJ",
            "V",
            "PG",
            "UNH",
        ]
        return trending_tickers[:limit]

    def get_current_stock_price(self, ticker: str) -> Optional[float]:
        return self.get_current_price(ticker)

    def _download_price_data(
        self, ticker: str, start_date: str, end_date: str, interval: str
    ):
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
        try:
            self._rate_limit_delay()  # Rate limiting
            df = self._download_price_data(ticker, start_date, end_date, interval)
            return df
        except Exception as e:
            print(f"Error fetching stock data for {ticker}: {e}")
            raise


def fetch_trending_stocks(limit: int = 10) -> List[Dict]:
    fetcher = StockFetcher()
    stocks = fetcher.get_trending_stocks(limit=limit)
    print(f"📊 Fetched {len(stocks)} trending stocks")
    return stocks


def fetch_current_stock_price(ticker: str) -> Optional[float]:
    fetcher = StockFetcher()
    price = fetcher.get_current_stock_price(ticker)
    if price:
        print(f"Stock price 💰 {ticker}: {price}")
    return price

from datetime import datetime, timedelta
from typing import Any, List, Optional, Union

import yfinance as yf

from live_trade_bench.fetchers.base_fetcher import BaseFetcher


class StockFetcher(BaseFetcher):
    def __init__(self, min_delay: float = 1.0, max_delay: float = 3.0):
        super().__init__(min_delay, max_delay)

    def fetch(
        self, mode: str, **kwargs: Any
    ) -> Union[List[str], Optional[float], Optional[str]]:
        if mode == "trending_stocks":
            return self.get_trending_stocks(limit=int(kwargs.get("limit", 15)))
        elif mode == "stock_price":
            ticker = kwargs.get("ticker")
            if ticker is None:
                raise ValueError("ticker is required for stock_price")
            date = kwargs.get("date")
            return self.get_price(str(ticker), date=date)
        elif mode == "company_url":
            ticker = kwargs.get("ticker")
            if ticker is None:
                raise ValueError("ticker is required for company_url")
            return self.get_company_url(str(ticker))
        else:
            raise ValueError(f"Unknown fetch mode: {mode}")

    def get_trending_stocks(self, limit: int = 15) -> List[str]:
        diversified_tickers = [
            "AAPL",
            "MSFT",
            "NVDA",
            "JPM",
            "V",
            "JNJ",
            "UNH",
            "PG",
            "KO",
            "XOM",
            "CAT",
            "WMT",
            "META",
            "TSLA",
            "AMZN",
        ]
        return diversified_tickers[:limit]

    def get_price(self, ticker: str, date: Optional[str] = None) -> Optional[float]:
        if date:
            return self._get_price_on_date(ticker, date)
        return self.get_current_price(ticker)

    def get_company_url(self, ticker: str) -> Optional[str]:
        try:
            stock = yf.Ticker(ticker)
            info = {}
            try:
                info = stock.info or {}
            except Exception:
                info = {}
            url = info.get("website") or info.get("website_url")
            if isinstance(url, str) and url.strip():
                u = url.strip()
                if not u.startswith("http://") and not u.startswith("https://"):
                    u = "https://" + u
                return u
        except Exception:
            pass
        # Fallback to Yahoo Finance
        return f"https://finance.yahoo.com/quote/{ticker}"

    def _download_price_data(
        self, ticker: str, start_date: str, end_date: str, interval: str
    ) -> Any:
        df = yf.download(
            tickers=ticker,
            start=start_date,
            end=end_date,
            interval=interval,
            progress=False,
            auto_adjust=True,
            prepost=True,
            threads=True,
        )
        if df.empty:
            print(
                f"No data for {ticker} from {start_date} to {end_date}, likely a holiday."
            )
            return df
        return df

    def get_current_price(self, ticker: str) -> Optional[float]:
        try:
            stock = yf.Ticker(ticker)
            try:
                fast_info = stock.fast_info
                if hasattr(fast_info, "last_price") and fast_info.last_price:
                    price = float(fast_info.last_price)
                    if price > 0:
                        return price
            except Exception:
                pass
            try:
                info = stock.info
                for field in ("currentPrice", "regularMarketPrice", "previousClose"):
                    if field in info and info[field]:
                        price = float(info[field])
                        if price > 0:
                            return price
            except Exception:
                pass
            try:
                history = stock.history(period="1d", interval="1m")
                if not history.empty:
                    latest_price = history["Close"].iloc[-1]
                    if latest_price and latest_price > 0:
                        return float(latest_price)
            except Exception:
                pass
            try:
                data = yf.download(ticker, period="1d", interval="1m", progress=False)
                if not data.empty:
                    latest_price = data["Close"].iloc[-1]
                    return float(latest_price)
            except Exception:
                pass
            return None
        except Exception:
            return None

    def _get_price_on_date(self, ticker: str, date: str) -> Optional[float]:
        try:
            start_date = date
            end_date_dt = datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)
            end_date = end_date_dt.strftime("%Y-%m-%d")
            df = self._download_price_data(ticker, start_date, end_date, interval="1d")
            if df is not None and not df.empty:
                for col in ("Close", "Adj Close", "close"):
                    if col in df.columns:
                        series = df[col]
                        try:
                            return float(series.to_numpy()[-1])
                        except Exception:
                            val = series.iloc[-1]
                            try:
                                return float(getattr(val, "item", lambda: val)())
                            except Exception:
                                continue
        except Exception:
            return None
        return None

    def fetch_stock_data(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
        interval: str = "1d",
    ) -> Any:
        self._rate_limit_delay()
        return self._download_price_data(ticker, start_date, end_date, interval)


def fetch_trending_stocks(limit: int = 15) -> List[str]:
    fetcher = StockFetcher()
    return fetcher.get_trending_stocks(limit=limit)


def fetch_current_stock_price(ticker: str) -> Optional[float]:
    fetcher = StockFetcher()
    return fetcher.get_price(ticker)


def fetch_stock_price_on_date(ticker: str, date: str) -> Optional[float]:
    fetcher = StockFetcher()
    return fetcher.get_price(ticker, date=date)


def fetch_stock_price(ticker: str, date: Optional[str] = None) -> Optional[float]:
    fetcher = StockFetcher()
    return fetcher.get_price(ticker, date=date)


def fetch_company_url(ticker: str) -> Optional[str]:
    fetcher = StockFetcher()
    return fetcher.get_company_url(ticker)

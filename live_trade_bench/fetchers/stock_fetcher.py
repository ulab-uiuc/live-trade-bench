from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import yfinance as yf

from live_trade_bench.fetchers.base_fetcher import BaseFetcher


class StockFetcher(BaseFetcher):
    def __init__(self, min_delay: float = 1.0, max_delay: float = 3.0):
        super().__init__(min_delay, max_delay)

    def fetch(self, mode: str, **kwargs: Any) -> Union[List[str], Optional[float]]:
        if mode == "trending_stocks":
            return self.get_trending_stocks(limit=int(kwargs.get("limit", 15)))
        elif mode == "stock_price":
            ticker = kwargs.get("ticker")
            if ticker is None:
                raise ValueError("ticker is required for stock_price")
            date = kwargs.get("date")
            return self.get_price(str(ticker), date=date)
        else:
            raise ValueError(f"Unknown fetch mode: {mode}")

    def get_trending_stocks(self, limit: int = 15) -> List[str]:
        tickers = [
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
        return tickers[:limit]

    def get_price(self, ticker: str, date: Optional[str] = None) -> Optional[float]:
        if date:
            return self._get_price_on_date(ticker, date)
        return self.get_current_price(ticker)

    def get_price_with_history(
        self, ticker: str, date: Optional[str] = None
    ) -> Dict[str, Any]:
        if date:
            end_date = datetime.strptime(date, "%Y-%m-%d")
        else:
            end_date = datetime.now()
        start_date = end_date - timedelta(days=20)

        price_data = self._download_price_data(
            ticker,
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d"),
            interval="1d",
        )

        price_history = []
        if price_data is not None and not price_data.empty:
            for idx, row in price_data.iterrows():
                price_history.append(
                    {
                        "date": idx.strftime("%Y-%m-%d"),
                        "price": float(row["Close"].iloc[0]) if "Close" in row else 0.0,
                        "volume": int(row["Volume"].iloc[0]) if "Volume" in row else 0,
                    }
                )

        return {
            "current_price": self.get_price(ticker, date),
            "price_history": price_history,
            "ticker": ticker,
        }

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
            print(f"No data for {ticker} from {start_date} to {end_date}.")
        return df

    def get_current_price(self, ticker: str) -> Optional[float]:
        stock = yf.Ticker(ticker)
        try:
            fast_info = stock.fast_info
            if hasattr(fast_info, "last_price") and fast_info.last_price:
                price = float(fast_info.last_price)
                if price > 0:
                    return price
        except Exception:
            pass
        return None

    def _get_price_on_date(self, ticker: str, date: str) -> Optional[float]:
        try:
            start_date = date
            end_date = (
                datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)
            ).strftime("%Y-%m-%d")
            df = self._download_price_data(ticker, start_date, end_date, interval="1d")
            if df is not None and not df.empty:
                for col in ("Close", "Adj Close", "close"):
                    if col in df.columns:
                        try:
                            return float(df[col].iloc[0])
                        except Exception:
                            continue
        except Exception:
            return None
        return None


def fetch_trending_stocks(limit: int = 15) -> List[str]:
    return StockFetcher().get_trending_stocks(limit=limit)


def fetch_stock_price_with_history(
    ticker: str, date: Optional[str] = None
) -> Dict[str, Any]:
    return StockFetcher().get_price_with_history(ticker, date=date)

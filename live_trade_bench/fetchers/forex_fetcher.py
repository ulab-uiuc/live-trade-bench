"""
Forex data fetcher built on top of yfinance.

This fetcher mirrors the interface of other fetchers in the project so the
portfolio system can treat FX pairs the same way as stocks or crypto. It uses
Yahoo Finance symbols (e.g., EURUSD=X) underneath and exposes utilities for
major currency pairs, price snapshots, and short history windows that feed the
LLM agents.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import yfinance as yf

from .base_fetcher import BaseFetcher


class ForexFetcher(BaseFetcher):
    """Fetcher for major forex pairs using Yahoo Finance."""

    # Ordered by global trading volume / relevance
    MAJOR_PAIRS: List[str] = [
        "EURUSD",
        "USDJPY",
        "GBPUSD",
        "USDCHF",
        "AUDUSD",
        "USDCAD",
        "NZDUSD",
        "EURJPY",
        "EURGBP",
        "EURCHF",
        "AUDJPY",
        "GBPJPY",
        "CHFJPY",
        "EURNZD",
        "USDMXN",
    ]

    def __init__(self, min_delay: float = 0.5, max_delay: float = 1.5) -> None:
        super().__init__(min_delay, max_delay)

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _to_yahoo_symbol(pair: str) -> str:
        clean = pair.upper().replace("=X", "")
        return f"{clean}=X"

    @staticmethod
    def _split_pair(pair: str) -> Dict[str, str]:
        clean = pair.upper().replace("=X", "")
        base, quote = clean[:3], clean[3:]
        return {"base": base, "quote": quote}

    # ------------------------------------------------------------------- public
    def get_major_pairs(self, limit: int = 10) -> List[str]:
        return self.MAJOR_PAIRS[:limit]

    def get_price(self, pair: str, date: Optional[str] = None) -> Optional[float]:
        if date:
            return self._get_price_on_date(pair, date)
        return self._get_current_price(pair)

    def get_price_with_history(
        self,
        pair: str,
        lookback_days: int = 7,
        date: Optional[str] = None,
    ) -> Dict[str, Any]:
        if date:
            end_date = datetime.strptime(date, "%Y-%m-%d") - timedelta(days=1)
        else:
            end_date = datetime.now(timezone.utc)

        start_date = end_date - timedelta(days=lookback_days)
        price_data = self._download_price_data(
            pair,
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d"),
            interval="1d",
        )

        history: List[Dict[str, Any]] = []
        if price_data is not None and not price_data.empty:
            for idx, row in price_data.iterrows():
                history.append(
                    {
                        "date": idx.strftime("%Y-%m-%d"),
                        "price": float(row["Close"]) if "Close" in row else 0.0,
                        "volume": int(row["Volume"]) if "Volume" in row else 0,
                    }
                )

        return {
            "pair": pair,
            "current_price": self.get_price(pair, date),
            "price_history": history,
            **self._split_pair(pair),
        }

    def fetch(self, mode: str, **kwargs: Any) -> Any:
        if mode == "trending_pairs":
            return self.get_major_pairs(limit=int(kwargs.get("limit", 10)))
        if mode == "price":
            pair = kwargs.get("pair")
            if not pair:
                raise ValueError("pair is required for forex price fetch")
            return self.get_price(str(pair), date=kwargs.get("date"))
        if mode == "price_with_history":
            pair = kwargs.get("pair")
            if not pair:
                raise ValueError("pair is required for price_with_history")
            return self.get_price_with_history(
                str(pair),
                lookback_days=int(kwargs.get("lookback_days", 7)),
                date=kwargs.get("date"),
            )
        raise ValueError(f"Unknown fetch mode for ForexFetcher: {mode}")

    # ----------------------------------------------------------------- internals
    def _get_current_price(self, pair: str) -> Optional[float]:
        symbol = self._to_yahoo_symbol(pair)
        ticker = yf.Ticker(symbol)
        try:
            fast_info = ticker.fast_info
            price = getattr(fast_info, "last_price", None)
            if price:
                price_float = float(price)
                if price_float > 0:
                    return price_float
        except Exception:
            pass

        try:
            history = ticker.history(period="5d", interval="1h")
            if not history.empty and "Close" in history:
                return float(history["Close"].iloc[-1])
        except Exception:
            pass
        return None

    def _download_price_data(
        self, pair: str, start_date: str, end_date: str, interval: str
    ):
        symbol = self._to_yahoo_symbol(pair)
        try:
            df = yf.download(
                tickers=symbol,
                start=start_date,
                end=(datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)).strftime(
                    "%Y-%m-%d"
                ),
                interval=interval,
                progress=False,
                auto_adjust=True,
                prepost=True,
                threads=True,
            )
            return df
        except Exception:
            return None

    def _get_price_on_date(self, pair: str, date: str) -> Optional[float]:
        try:
            start_date = datetime.strptime(date, "%Y-%m-%d") - timedelta(days=1)
            end_date = datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)
            df = self._download_price_data(
                pair,
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d"),
                interval="1d",
            )
            if df is not None and not df.empty:
                for col in ("Close", "Adj Close", "close"):
                    if col in df.columns and not df[col].empty:
                        try:
                            return float(df[col].iloc[-1])
                        except Exception:
                            continue
        except Exception:
            return None
        return None


def fetch_trending_fx_pairs(limit: int = 10) -> List[str]:
    return ForexFetcher().get_major_pairs(limit=limit)


def fetch_fx_price_with_history(
    pair: str, lookback_days: int = 7, date: Optional[str] = None
) -> Dict[str, Any]:
    return ForexFetcher().get_price_with_history(pair, lookback_days, date)


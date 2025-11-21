"""Tests for the ForexFetcher helper."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
import pytest

from live_trade_bench.fetchers.forex_fetcher import ForexFetcher


def test_get_major_pairs_respects_limit() -> None:
    fetcher = ForexFetcher()
    pairs = fetcher.get_major_pairs(limit=3)
    assert pairs == ["EURUSD", "USDJPY", "GBPUSD"]
    assert len(pairs) == 3


def test_get_price_with_history(monkeypatch: pytest.MonkeyPatch) -> None:
    fetcher = ForexFetcher()

    df = pd.DataFrame(
        {
            "Close": [1.10, 1.12, 1.15],
            "Volume": [1_000, 1_200, 1_500],
        },
        index=pd.to_datetime(
            ["2024-01-01", "2024-01-02", "2024-01-03"], utc=True
        ),
    )

    def fake_download(
        self: ForexFetcher, pair: str, start: str, end: str, interval: str
    ) -> Any:
        assert pair == "EURUSD"
        assert interval == "1d"
        return df

    def fake_get_price(
        self: ForexFetcher, pair: str, date: str | None = None
    ) -> float:
        assert pair == "EURUSD"
        return 1.2345

    monkeypatch.setattr(ForexFetcher, "_download_price_data", fake_download)
    monkeypatch.setattr(ForexFetcher, "get_price", fake_get_price)

    payload = fetcher.get_price_with_history("EURUSD", lookback_days=3)

    assert payload["pair"] == "EURUSD"
    assert payload["base"] == "EUR"
    assert payload["quote"] == "USD"
    assert payload["current_price"] == pytest.approx(1.2345)
    assert len(payload["price_history"]) == 3
    assert payload["price_history"][0]["price"] == pytest.approx(1.10)


def test_fetch_trending_pairs_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    fetcher = ForexFetcher()

    monkeypatch.setattr(fetcher, "get_major_pairs", lambda limit=10: ["EURUSD"])

    result = fetcher.fetch("trending_pairs", limit=1)
    assert result == ["EURUSD"]


def test_fetch_price_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    fetcher = ForexFetcher()

    monkeypatch.setattr(fetcher, "get_price", lambda pair, date=None: 1.1111)

    price = fetcher.fetch("price", pair="EURUSD")
    assert price == pytest.approx(1.1111)


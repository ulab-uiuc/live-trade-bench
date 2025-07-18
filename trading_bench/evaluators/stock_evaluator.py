# ----------------------------------------------
# trading/stock.py
# ----------------------------------------------
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List

from trading_bench.fetchers.stock_fetcher import fetch_stock_data  # type: ignore
from trading_bench.evaluators.action import StockAction, parse_actions
from trading_bench.evaluators.base_evaluator import BaseEvaluator, PositionTracker


class StockEvaluator(BaseEvaluator):
    """Stock trading evaluator using historical price data."""

    def __init__(self, risk_free_rate: float = 0.02):
        super().__init__(risk_free_rate)
        self._pt = PositionTracker()

    # --------------------------------------------------
    def _fetch_price(self, ticker: str, date: str) -> float | None:
        """Fetch stock price for specific date."""
        try:
            data = fetch_stock_data(
                ticker, start_date=date, end_date=date, resolution="D"
            )
            return data[date]["close"] if data and date in data else None
        except Exception:
            return None

    # --------------------------------------------------
    def _fetch_latest_prices(self, tickers: List[str]) -> Dict[str, float]:
        """Fetch latest prices for tickers."""
        prices = {}
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        for ticker in tickers:
            try:
                data = fetch_stock_data(
                    ticker,
                    start_date=start_date.strftime("%Y-%m-%d"),
                    end_date=end_date.strftime("%Y-%m-%d"),
                    resolution="D",
                )
                if data:
                    latest_date = max(data.keys())
                    prices[ticker] = data[latest_date]["close"]
            except Exception:
                continue
        return prices

    # --------------------------------------------------
    def evaluate(self, actions, **kw) -> Dict[str, Any]:
        acts = parse_actions(actions, StockAction)

        realised = vol = trades = 0.0

        for a in acts:
            price = a.price if a.price > 0 else self._fetch_price(a.ticker, a.timestamp)
            if price is None:
                continue

            if a.action == "buy":
                self._pt.update(a.ticker, "buy", price, a.quantity)
                vol += a.quantity * price
            else:  # sell
                pos = self._pt.get(a.ticker)
                if pos["quantity"] >= a.quantity:
                    realised += (price - pos["avg_price"]) * a.quantity
                    self._pt.update(a.ticker, "sell", price, a.quantity)
                    vol += a.quantity * price
            trades += 1

        # Get unrealised P&L
        active_tickers = [t for t, p in self._pt.all().items() if p["quantity"] > 0]
        latest_prices = (
            self._fetch_latest_prices(active_tickers) if active_tickers else {}
        )
        unrealised = self._pt.unrealised(latest_prices)

        total = realised + unrealised
        res = {
            **self._basic(total, int(trades), vol),
            "realized_pnl": realised,
            "unrealized_pnl": unrealised,
            "evaluator_type": self.get_evaluator_type(),
        }

        self._print_summary(res)
        self._save(res)
        return res

    # --------------------------------------------------
    def get_evaluator_type(self) -> str:  # noqa: D401
        return "stock"


def eval_stock(actions):  # type: ignore
    """Legacy function for backward compatibility."""
    return StockEvaluator().evaluate(actions)["total_pnl"]

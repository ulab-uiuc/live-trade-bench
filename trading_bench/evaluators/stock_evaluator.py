# ----------------------------------------------
# trading/stock.py
# ----------------------------------------------
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List

<<<<<<< HEAD
from ..fetchers.stock_fetcher import fetch_stock_data  # type: ignore
from .base_evaluator import BaseEvaluator, PositionTracker
from .utils import StockAction, parse_actions


class StockEvaluator(BaseEvaluator):
    """Stock trading evaluator using historical price data."""

    def __init__(self, risk_free_rate: float = 0.02):
        super().__init__(risk_free_rate)
        self._pt = PositionTracker()
||||||| 8187782
from trading_bench.fetchers.stock_fetcher import fetch_stock_data


def eval(actions: str | dict | list[dict]) -> float:
    """
    Simple evaluator that takes JSON format actions and returns total benefits.
    Automatically fetches latest price data to calculate benefits.

    Args:
        actions: JSON string or dict/list of actions with format:
                {
                    "ticker": "AAPL",
                    "action": "buy" or "sell",
                    "timestamp": "2025-01-01",
                    "price": 150.0,  # optional, will fetch if not provided
                    "quantity": 1    # optional, defaults to 1
                }

    Returns:
        float: Total benefits/returns compared to latest price
    """
    # Parse JSON if string
    if isinstance(actions, str):
        actions = json.loads(actions)

    # Convert single action to list
    if isinstance(actions, dict):
        actions = [actions]

    total_benefits = 0.0
    positions = {}  # Track positions: ticker -> {quantity, avg_price, timestamps}

    for action in actions:
        ticker = action["ticker"]
        action_type = action["action"].lower()
        timestamp = action["timestamp"]
        quantity = action.get("quantity", 1)

        # Get price for the action
        if "price" in action:
            price = action["price"]
        else:
            # Fetch price data for the action date
            price_data = fetch_stock_data(
                ticker=ticker, start_date=timestamp, end_date=timestamp, resolution="D"
            )
            if price_data and timestamp in price_data:
                price = price_data[timestamp]["close"]
            else:
                print(f"Warning: Could not fetch price for {ticker} on {timestamp}")
                continue
=======
from ..fetchers.stock_fetcher import fetch_stock_data  # type: ignore
from .action import StockAction, parse_actions
from .base_evaluator import BaseEvaluator, PositionTracker


class StockEvaluator(BaseEvaluator):
    """Stock trading evaluator using historical price data."""

    def __init__(self, risk_free_rate: float = 0.02):
        super().__init__(risk_free_rate)
        self._pt = PositionTracker()
>>>>>>> ce16017c508d783b9df241f101ad2be05478002e

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

<<<<<<< HEAD
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


# one‑liner helper
def eval(actions):  # type: ignore
    """Legacy function for backward compatibility."""
    return StockEvaluator().evaluate(actions)["total_pnl"]
||||||| 8187782
    def evaluate(self, actions: str | dict | list[dict]) -> float:
        """Wrapper for the new eval function"""
        return eval(actions)
=======
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
>>>>>>> ce16017c508d783b9df241f101ad2be05478002e

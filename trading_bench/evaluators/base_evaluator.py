# ----------------------------------------------
# trading/base.py
# ----------------------------------------------
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from statistics import pstdev
from typing import Any, Dict, List, Sequence


class PositionTracker:
    """Track running positions per instrument (avg price & qty)."""

    def __init__(self) -> None:
        self._pos: Dict[str, Dict[str, float | list]] = {}

    # --------------------------------------------------
    def update(self, inst: str, action: str, price: float, qty: float) -> None:
        p = self._pos.setdefault(inst, {"quantity": 0.0, "avg_price": 0.0})
        if action == "buy":
            new_qty = p["quantity"] + qty
            p["avg_price"] = ((p["avg_price"] * p["quantity"]) + price * qty) / new_qty
            p["quantity"] = new_qty
        elif action == "sell":
            p["quantity"] -= qty
            if p["quantity"] < 0:
                raise ValueError(f"Negative position in {inst}")

    # --------------------------------------------------
    def get(self, inst: str) -> Dict[str, float]:
        return self._pos.get(inst, {"quantity": 0.0, "avg_price": 0.0})

    def all(self) -> Dict[str, Dict[str, float]]:
        return self._pos

    # --------------------------------------------------
    def unrealised(self, prices: Dict[str, float]) -> float:
        pnl = 0.0
        for inst, p in self._pos.items():
            if p["quantity"] > 0 and inst in prices:
                pnl += (prices[inst] - p["avg_price"]) * p["quantity"]
        return pnl


class BaseEvaluator(ABC):
    """Common metrics & history for any evaluator subtype."""

    def __init__(self, risk_free_rate: float = 0.02) -> None:
        self.risk_free_rate = risk_free_rate
        self._history: List[Dict[str, Any]] = []

    # --------------------------------------------------
    def _sharpe(self, rtn: float, vols: Sequence[float] | None = None) -> float:
        vol = pstdev(vols) if vols else abs(rtn) * 0.2
        return 0.0 if vol == 0 else (rtn - self.risk_free_rate) / vol

    # --------------------------------------------------
    def _basic(self, pnl: float, trades: int, volume: float) -> Dict[str, Any]:
        return {
            "total_pnl": pnl,
            "total_trades": trades,
            "total_volume": volume,
            "average_trade_size": volume / trades if trades else 0.0,
            "sharpe_ratio": self._sharpe(pnl),
        }

    # --------------------------------------------------
    def _print_summary(self, r: Dict[str, Any]) -> None:  # noqa: N802
        print("\n📈 Evaluation Summary\n" + "=" * 28)
        print(f"Total   P&L: ${r['total_pnl']:.2f}")
        if "realized_pnl" in r:
            print(f"Realised P&L: ${r['realized_pnl']:.2f}")
        if "unrealized_pnl" in r:
            print(f"Unrealised P&L: ${r['unrealized_pnl']:.2f}")
        print(f"Trades         : {r['total_trades']}")
        print(f"Avg trade size : ${r['average_trade_size']:.2f}")
        print(f"Sharpe ratio   : {r['sharpe_ratio']:.2f}")

    # --------------------------------------------------
    def _save(self, res: Dict[str, Any]) -> None:
        self._history.append({"ts": datetime.utcnow().isoformat(), **res})

    # --------------------------------------------------
    @abstractmethod
    def evaluate(self, actions, **kw) -> Dict[str, Any]:
        ...

    @abstractmethod
    def get_evaluator_type(self) -> str:  # noqa: D401
        ...

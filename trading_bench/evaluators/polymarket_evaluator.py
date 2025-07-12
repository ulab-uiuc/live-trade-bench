# ----------------------------------------------
# trading/polymarket.py
# ----------------------------------------------
from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Any, Dict

from .base_evaluator import BaseEvaluator, PositionTracker
from .utils import PolymarketAction, parse_actions


class PolymarketEvaluator(BaseEvaluator):
    """Binary prediction‑market evaluator (YES/NO shares range 0‑1)."""

    def __init__(self, risk_free_rate: float = 0.02):
        super().__init__(risk_free_rate)
        self._pt = PositionTracker()

    # --------------------------------------------------
    def _sim_price(self, avg: float) -> float:
        return max(0.0, min(1.0, avg * (1 + random.uniform(-0.1, 0.1))))

    # --------------------------------------------------
    def evaluate(
        self, actions, market_outcomes: Dict[str, Dict[str, str]] | None = None, **kw
    ) -> Dict[str, Any]:
        acts = parse_actions(actions, PolymarketAction)
        if market_outcomes is None:
            market_outcomes = {
                a.market_id: {
                    "result": random.choice(["yes", "no"]),
                    "resolution_date": (
                        datetime.utcnow() + timedelta(days=random.randint(1, 365))
                    ).strftime("%Y-%m-%d"),
                }
                for a in acts
            }
        realised = unrealised = vol = trades = wins = 0.0
        for a in acts:
            key = f"{a.market_id}:{a.outcome}"
            if a.action == "buy":
                self._pt.update(key, "buy", a.price, a.quantity)
                vol += a.quantity * a.price
            else:  # sell
                pos = self._pt.get(key)
                if pos["quantity"] >= a.quantity:
                    realised += (a.price - pos["avg_price"]) * a.quantity
                    self._pt.update(key, "sell", a.price, a.quantity)
                    vol += a.quantity * a.price
            trades += 1
        # compute unrealised & accuracy
        for mid, outcome in market_outcomes.items():
            for side in ("yes", "no"):
                key = f"{mid}:{side}"
                pos = self._pt.get(key)
                if pos["quantity"] == 0:
                    continue
                final_val = 1.0 if outcome["result"] == side else 0.0
                if outcome["result"] not in ("yes", "no"):
                    final_val = self._sim_price(pos["avg_price"])
                unrealised += (final_val - pos["avg_price"]) * pos["quantity"]
                if final_val == 1.0:
                    wins += 1
        total = realised + unrealised
        res = {
            **self._basic(total, int(trades), vol),
            "realized_pnl": realised,
            "unrealized_pnl": unrealised,
            "market_outcomes": market_outcomes,
            "evaluator_type": self.get_evaluator_type(),
            "prediction_accuracy": wins / len(market_outcomes)
            if market_outcomes
            else 0.0,
        }
        self._print_summary(res)
        self._save(res)
        return res

    # --------------------------------------------------
    def get_evaluator_type(self) -> str:  # noqa: D401
        return "polymarket"


# one‑liner helper


def eval_polymarket(actions, market_outcomes=None):  # type: ignore
    return PolymarketEvaluator().evaluate(actions, market_outcomes)

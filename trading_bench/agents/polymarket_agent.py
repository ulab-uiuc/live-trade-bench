from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from ..accounts import PolymarketAccount, PolymarketAction
from .base_agent import BaseAgent


class LLMPolyMarketAgent(
    BaseAgent[PolymarketAction, PolymarketAccount, Dict[str, Any]]
):
    """Active prediction market trading agent for market analysis and trading."""

    def __init__(self, name: str, model_name: str = "gpt-4o-mini") -> None:
        super().__init__(name, model_name)

    def _extract_id_price(self, data: Dict[str, Any]) -> Tuple[str, float]:
        if "id" in data and "price" in data:
            return str(data["id"]), float(data["price"])
        return str(data["market_id"]), float(data["price"])

    def _prepare_analysis_data(
        self, data: Dict[str, Any], account: PolymarketAccount
    ) -> str:
        _id, price = self._extract_id_price(data)
        yes_price = float(data.get("yes_price", price))
        no_price = float(data.get("no_price", 1.0 - yes_price))
        question = data.get("question", _id)
        category = data.get("category", "Unknown")

        prev = self.prev_price(_id)
        pct = 0.0 if prev is None else ((price - prev) / prev) * 100.0
        trend = "up" if pct > 0 else ("down" if pct < 0 else "flat")
        hist = ", ".join(f"{p:.2f}" for p in self.history_tail(_id, 5))

        pos = account.get_active_positions()
        yes_q = pos.get(f"{_id}_yes").quantity if f"{_id}_yes" in pos else 0
        no_q = pos.get(f"{_id}_no").quantity if f"{_id}_no" in pos else 0

        # Calculate trading signals
        is_yes_cheap = yes_price < 0.4
        is_yes_expensive = yes_price > 0.6
        has_yes_position = yes_q > 0
        has_no_position = no_q > 0

        signals = []
        if is_yes_cheap:
            signals.append("🟢 YES looks undervalued")
        if is_yes_expensive:
            signals.append("🔴 YES looks overvalued")
        if has_yes_position:
            signals.append(f"📊 Holding {yes_q} YES shares")
        if has_no_position:
            signals.append(f"📊 Holding {no_q} NO shares")

        return (
            f"MARKET: {question}\n"
            f"CATEGORY: {category}\n"
            f"PRICES: YES {yes_price:.3f} ({yes_price*100:.1f}%) | NO {no_price:.3f} ({no_price*100:.1f}%)\n"
            f"TREND: {trend} ({pct:+.2f}%)\n"
            f"HISTORY: [{hist}]\n"
            f"CASH: ${account.cash_balance:.2f}\n"
            f"POSITIONS: YES {yes_q} | NO {no_q}\n"
            f"SIGNALS: {' | '.join(signals) if signals else 'No clear signals'}"
        )

    def _create_action_from_response(
        self, parsed: Dict[str, Any], _id: str, price: float
    ) -> Optional[PolymarketAction]:
        action = (parsed.get("action") or "hold").lower()
        outcome = (parsed.get("outcome") or "yes").lower()
        qty = int(parsed.get("quantity", 0))  # HOLD can have 0 quantity
        conf = float(parsed.get("confidence", 0.5))

        # For non-hold actions, require positive quantity
        if action == "hold" or qty <= 0:
            return None

        return PolymarketAction(
            market_id=_id,
            outcome=outcome,
            action=action,
            timestamp=datetime.now().isoformat(),
            price=price,
            quantity=qty,
            confidence=conf,
        )

    def _get_system_prompt(self, analysis_data: str) -> str:
        return (
            "You are an active prediction market trader. Analyze the market and take positions.\n"
            f"Market Analysis: {analysis_data}\n\n"
            "TRADING RULES:\n"
            "- If YES price < 0.4 and you think it should be higher: BUY YES (quantity 5-15)\n"
            "- If YES price > 0.6 and you think it should be lower: BUY NO (quantity 5-15)\n"
            "- If you hold opposite position: SELL to close (quantity 1-10)\n"
            "- Only HOLD if market price seems fair (confidence < 0.3)\n"
            "- Be decisive! Take positions based on your analysis.\n\n"
            "Return VALID JSON ONLY:\n"
            "{\n"
            ' "action": "buy|sell|hold",\n'
            ' "outcome": "yes|no",\n'
            ' "quantity": <int>,\n'
            ' "confidence": <0.0-1.0>,\n'
            ' "reasoning": "<brief explanation>"\n'
            "}"
        )


def create_polymarket_agent(
    name: str, model_name: str = "gpt-4o-mini"
) -> LLMPolyMarketAgent:
    return LLMPolyMarketAgent(name, model_name)

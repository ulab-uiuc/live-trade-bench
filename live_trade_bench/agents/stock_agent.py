from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from ..accounts import StockAccount, StockAction
from .base_agent import BaseAgent


class LLMStockAgent(BaseAgent[StockAction, StockAccount, Dict[str, Any]]):
    """Active stock trading agent for market analysis and trading."""

    def __init__(self, name: str, model_name: str = "gpt-4o-mini") -> None:
        super().__init__(name, model_name)

    def _extract_id_price(self, data: Dict[str, Any]) -> Tuple[str, float]:
        if "id" in data and "price" in data:
            return str(data["id"]), float(data["price"])
        return str(data["ticker"]), float(data["current_price"])

    def _prepare_market_analysis(self, data: Dict[str, Any]) -> str:
        """Prepare market-specific analysis for stocks."""
        _id, price = self._extract_id_price(data)
        prev = self.prev_price(_id)
        pct = 0.0 if prev is None else ((price - prev) / prev) * 100.0
        trend = "up" if pct > 0 else ("down" if pct < 0 else "flat")
        hist = ", ".join(f"{p:.2f}" for p in self.history_tail(_id, 5))

        pos_txt = "See account section"

        # Calculate trading signals
        is_trending_up = pct > 2.0
        is_trending_down = pct < -2.0

        signals = []
        if is_trending_up:
            signals.append("🟢 Strong uptrend")
        elif is_trending_down:
            signals.append("🔴 Strong downtrend")
        else:
            signals.append("🟡 Sideways movement")

        return (
            f"STOCK: {_id}\n"
            f"PRICE: ${price:.2f}\n"
            f"CHANGE: {pct:+.2f}% ({trend})\n"
            f"HISTORY: [{hist}]\n"
            f"CURRENT POSITION: {pos_txt}\n"
            f"SIGNALS: {' | '.join(signals)}"
        )

    def _create_news_query(self, _id: str, data: Dict[str, Any]) -> str:
        """Create stock-specific news query."""
        return f"{_id} stock earnings news"

    def _create_action_from_response(
        self, parsed: Dict[str, Any], ticker: str, current_price: float
    ) -> Optional[StockAction]:
        action = (parsed.get("action") or "hold").lower()
        qty = int(parsed.get("quantity", 0))  # HOLD can have 0 quantity
        conf = float(parsed.get("confidence", 0.5))

        if action == "hold" or qty <= 0:
            return None

        return StockAction(
            ticker=ticker,
            action=action,
            timestamp=datetime.now().isoformat(),
            price=current_price,
            quantity=qty,
            confidence=conf,
        )

    def _get_prompt(self, analysis_data: str) -> str:
        return (
            "You are a thoughtful stock trader. Make data-driven investment decisions.\n"
            f"Stock Analysis: {analysis_data}\n\n"
            "TRADING PHILOSOPHY:\n"
            "- Focus on momentum, fundamentals, and market sentiment\n"
            "- Consider both technical patterns and news catalysts\n"
            "- Diversify risk across your portfolio when possible\n"
            "- Cut losses early, let winners run when appropriate\n"
            "- Adapt your strategy based on market conditions\n\n"
            "- Try to be active and buy/sell more often\n\n"
            "POSITION SIZING GUIDANCE:\n"
            "- High conviction trades: Larger positions (8-15 shares)\n"
            "- Moderate conviction: Standard positions (3-8 shares)\n"
            "- Low conviction: Small positions (1-3 shares) or HOLD\n"
            "- Consider your existing exposure to avoid concentration risk\n\n"
            "Return VALID JSON ONLY:\n"
            "{\n"
            ' "action": "buy|sell|hold",\n'
            ' "quantity": <int>,\n'
            ' "confidence": <0.0-1.0>,\n'
            ' "reasoning": "<brief explanation>"\n'
            "}"
        )


def create_stock_agent(name: str, model_name: str = "gpt-4o-mini") -> LLMStockAgent:
    return LLMStockAgent(name, model_name)

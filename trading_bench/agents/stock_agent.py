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

    def _prepare_analysis_data(
        self, data: Dict[str, Any], account: StockAccount
    ) -> str:
        _id, price = self._extract_id_price(data)
        prev = self.prev_price(_id)
        pct = 0.0 if prev is None else ((price - prev) / prev) * 100.0
        trend = "up" if pct > 0 else ("down" if pct < 0 else "flat")
        hist = ", ".join(f"{p:.2f}" for p in self.history_tail(_id, 5))

        pos = account.get_active_positions().get(_id)
        pos_txt = f"{pos.quantity}@{pos.avg_price:.2f}" if pos else "none"

        # Calculate trading signals
        is_trending_up = pct > 2.0
        is_trending_down = pct < -2.0
        has_position = pos is not None
        
        signals = []
        if is_trending_up:
            signals.append("🟢 Strong uptrend")
        elif is_trending_down:
            signals.append("🔴 Strong downtrend")
        else:
            signals.append("🟡 Sideways movement")
            
        if has_position:
            profit_loss = (price - pos.avg_price) * pos.quantity if pos else 0
            signals.append(f"📊 P&L: ${profit_loss:+.2f}")
            
        return (
            f"STOCK: {_id}\n"
            f"PRICE: ${price:.2f}\n"
            f"CHANGE: {pct:+.2f}% ({trend})\n"
            f"CASH: ${account.cash_balance:.2f}\n"
            f"POSITION: {pos_txt}\n"
            f"SIGNALS: {' | '.join(signals)}"
        )

    def _create_action_from_response(
        self, parsed: Dict[str, Any], ticker: str, current_price: float
    ) -> Optional[StockAction]:
        action = (parsed.get("action") or "hold").lower()
        qty = int(parsed.get("quantity", 0))  # HOLD can have 0 quantity
        conf = float(parsed.get("confidence", 0.5))
        
        # For non-hold actions, require positive quantity
        if action == 'hold' or qty <= 0:
            return None
            
        return StockAction(
            ticker=ticker,
            action=action,
            timestamp=datetime.now().isoformat(),
            price=current_price,
            quantity=qty,
            confidence=conf,
        )

    def _get_system_prompt(self, analysis_data: str) -> str:
        return (
            "You are an active stock trader. Analyze trends and take positions.\n"
            f"Stock Analysis: {analysis_data}\n\n"
            "TRADING RULES:\n"
            "- If stock is trending UP (>2%): BUY (quantity 5-10)\n"
            "- If stock is trending DOWN (<-2%): SELL (quantity 3-8)\n"
            "- If you have position and trend reverses: SELL to close\n"
            "- Only HOLD if trend is flat (<2% change) and no clear signal\n"
            "- Be active! Stock markets reward decisive trading.\n\n"
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


from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from ..accounts import StockAccount
from .base_agent import BaseAgent


class LLMStockAgent(BaseAgent[StockAccount, Dict[str, Any]]):
    """Active stock trading agent for market analysis and portfolio allocation."""

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

    def _create_portfolio_allocation_from_response(
        self, parsed: Dict[str, Any], ticker: str, current_price: float
    ) -> Optional[Dict[str, float]]:
        """Create portfolio allocation from LLM response."""
        allocation = float(parsed.get("allocation", 0.0))
        confidence = float(parsed.get("confidence", 0.5))
        
        # Validate allocation (0.0 to 1.0)
        if allocation < 0.0 or allocation > 1.0:
            print(f"⚠️ Invalid allocation {allocation} for {ticker}, using 0.0")
            allocation = 0.0
        
        if allocation == 0.0:
            return None  # No allocation change
        
        return {
            "ticker": ticker,
            "allocation": allocation,
            "confidence": confidence,
            "reasoning": parsed.get("reasoning", "Portfolio allocation decision")
        }

    def _get_portfolio_prompt(self, analysis_data: str) -> str:
        return (
            "You are a thoughtful portfolio manager. Make data-driven portfolio allocation decisions.\n"
            f"Stock Analysis: {analysis_data}\n\n"
            "PORTFOLIO MANAGEMENT PHILOSOPHY:\n"
            "- Focus on risk-adjusted returns and diversification\n"
            "- Consider market momentum, fundamentals, and sentiment\n"
            "- Balance growth and value opportunities\n"
            "- Maintain appropriate position sizes based on conviction\n"
            "- Adapt allocations based on changing market conditions\n\n"
            "ALLOCATION GUIDANCE:\n"
            "- High conviction (>0.8): 15-25% of portfolio\n"
            "- Medium conviction (0.5-0.8): 8-15% of portfolio\n"
            "- Low conviction (<0.5): 3-8% of portfolio or 0%\n"
            "- Consider existing exposure to avoid concentration risk\n\n"
            "Return VALID JSON ONLY:\n"
            "{\n"
            ' "allocation": <0.0-1.0>,\n'
            ' "confidence": <0.0-1.0>,\n'
            ' "reasoning": "<brief explanation of allocation decision>"\n'
            "}"
        )


def create_stock_agent(name: str, model_name: str = "gpt-4o-mini") -> LLMStockAgent:
    """Create a new stock trading agent."""
    return LLMStockAgent(name, model_name)

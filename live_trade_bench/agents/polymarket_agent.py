from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from ..accounts import PolymarketAccount
from .base_agent import BaseAgent


class LLMPolyMarketAgent(BaseAgent[PolymarketAccount, Dict[str, Any]]):
    """Active prediction market trading agent for market analysis and portfolio allocation."""

    def __init__(self, name: str, model_name: str = "gpt-4o-mini") -> None:
        super().__init__(name, model_name)

    def _extract_id_price(self, data: Dict[str, Any]) -> Tuple[str, float]:
        if "id" in data and "price" in data:
            return str(data["id"]), float(data["price"])
        return str(data["market_id"]), float(data["price"])

    def _prepare_market_analysis(self, data: Dict[str, Any]) -> str:
        """Prepare market-specific analysis for Polymarket."""
        _id, price = self._extract_id_price(data)
        yes_price = float(data.get("yes_price", price))
        no_price = float(data.get("no_price", 1.0 - yes_price))
        question = data.get("question", _id)
        category = data.get("category", "Unknown")

        prev = self.prev_price(_id)
        pct = 0.0 if prev is None else ((price - prev) / prev) * 100.0
        trend = "up" if pct > 0 else ("down" if pct < 0 else "flat")
        hist = ", ".join(f"{p:.2f}" for p in self.history_tail(_id, 5))

        # Note: positions will be provided separately in account analysis
        yes_q = 0  # Placeholder - actual positions shown in account section
        no_q = 0

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
            f"CURRENT POSITIONS: YES {yes_q} | NO {no_q}\n"
            f"SIGNALS: {' | '.join(signals) if signals else 'No clear signals'}"
        )

    def _create_news_query(self, _id: str, data: Dict[str, Any]) -> str:
        """Create Polymarket-specific news query."""
        question = data.get("question", "")
        category = data.get("category", "")

        if question and len(question) > 10:
            key_terms = question.split()[:5]
            return " ".join(key_terms)
        elif category:
            return f"{category} prediction market"
        else:
            return f"polymarket {_id}"

    def _create_portfolio_allocation_from_response(
        self, parsed: Dict[str, Any], _id: str, price: float
    ) -> Optional[Dict[str, float]]:
        """Create portfolio allocation from LLM response."""
        allocation = float(parsed.get("allocation", 0.0))
        confidence = float(parsed.get("confidence", 0.5))
        outcome = (parsed.get("outcome") or "yes").lower()

        # Validate allocation (0.0 to 1.0)
        if allocation < 0.0 or allocation > 1.0:
            print(f"⚠️ Invalid allocation {allocation} for {_id}, using 0.0")
            allocation = 0.0

        if allocation == 0.0:
            return None  # No allocation change

        return {
            "market_id": _id,
            "outcome": outcome,
            "allocation": allocation,
            "confidence": confidence,
            "reasoning": parsed.get("reasoning", "Portfolio allocation decision"),
        }

    def _get_portfolio_prompt(self, analysis_data: str) -> str:
        return (
            "You are an intelligent prediction market portfolio manager. Use your judgment to analyze markets and allocate portfolio weights.\n"
            f"Market Analysis: {analysis_data}\n\n"
            "PORTFOLIO MANAGEMENT PHILOSOPHY:\n"
            "- Look for mispriced markets where your analysis differs from market consensus\n"
            "- Consider news, trends, and historical context in your decisions\n"
            "- Manage risk by sizing positions based on your confidence level\n"
            "- Don't allocate just to allocate - only act when you see clear opportunities\n"
            "- Learn from your positions and market feedback\n\n"
            "ALLOCATION GUIDANCE:\n"
            "- High confidence (>0.8): 15-25% of portfolio\n"
            "- Medium confidence (0.5-0.8): 8-15% of portfolio\n"
            "- Low confidence (<0.5): 3-8% of portfolio or 0%\n"
            "- Consider existing exposure to avoid concentration risk\n\n"
            "Return VALID JSON ONLY:\n"
            "{\n"
            ' "allocation": <0.0-1.0>,\n'
            ' "confidence": <0.0-1.0>,\n'
            ' "reasoning": "<brief explanation of allocation decision>"\n'
            "}"
        )


def create_polymarket_agent(
    name: str, model_name: str = "gpt-4o-mini"
) -> LLMPolyMarketAgent:
    """Create a new Polymarket trading agent."""
    return LLMPolyMarketAgent(name, model_name)

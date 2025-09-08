from __future__ import annotations

from typing import Any, Dict, Optional

from ..accounts import PolymarketAccount
from .base_agent import BaseAgent


class LLMPolyMarketAgent(BaseAgent[PolymarketAccount, Dict[str, Any]]):
    def __init__(self, name: str, model_name: str = "gpt-4o-mini") -> None:
        super().__init__(name, model_name)

    def _prepare_market_analysis(self, market_data: Dict[str, Dict[str, Any]]) -> str:
        analysis_parts = []
        for market_id, data in market_data.items():
            price = data.get("price", 0.0)
            question = data.get("question", market_id)
            category = data.get("category", "Unknown")
            yes_price = data.get("yes_price", price)
            no_price = data.get("no_price", 1.0 - yes_price)
            prev = self.prev_price(market_id)
            pct = 0.0 if prev is None else ((price - prev) / prev) * 100.0
            trend = "up" if pct > 0 else ("down" if pct < 0 else "flat")
            hist = ", ".join(f"{p:.3f}" for p in self.history_tail(market_id, 3))
            analysis_parts.append(
                f"{market_id}: {question[:50]}... | YES: {yes_price:.3f} NO: {no_price:.3f} | {pct:+.2f}% ({trend}) | Category: {category} | History: [{hist}]"
            )
            self._update_price_history(market_id, price)
        return "MARKET ANALYSIS:\n" + "\n".join(analysis_parts)

    def _create_news_query(self, market_id: str, data: Dict[str, Any]) -> str:
        question = data.get("question", "")
        category = data.get("category", "")
        if question and len(question) > 10:
            key_terms = question.split()[:5]
            return " ".join(key_terms)
        elif category:
            return f"{category} prediction market"
        else:
            return f"polymarket {market_id}"

    def _create_portfolio_allocation_from_response(
        self, parsed: Dict[str, Any], market_data: Dict[str, Dict[str, Any]]
    ) -> Optional[Dict[str, float]]:
        normalized = self._normalize_allocations_from_parsed(parsed)
        if not normalized:
            print("⚠️ No allocations found in LLM response")
            return None
        return normalized

    def _get_portfolio_prompt(
        self, analysis: str, market_data: Dict[str, Dict[str, Any]]
    ) -> str:
        market_list = list(market_data.keys())
        return (
            "You are a professional prediction market portfolio manager. Analyze the market data and generate a complete portfolio allocation.\n\n"
            f"Market Analysis:\n{analysis}\n\n"
            "PORTFOLIO MANAGEMENT PRINCIPLES:\n"
            "- Diversify across different market categories\n"
            "- Consider market sentiment and probability estimates\n"
            "- Balance high-confidence and speculative positions\n"
            "- Maintain appropriate position sizes\n"
            "- Total allocation must equal 100% (1.0)\n"
            "- CASH is a valid asset that should be allocated based on market conditions\n\n"
            f"AVAILABLE ASSETS: {market_list} + CASH\n\n"
            "CRITICAL: You must return ONLY valid JSON format. No additional text, explanations, or formatting.\n\n"
            "REQUIRED JSON FORMAT:\n"
            "{\n"
            ' "allocations": {\n'
            f'   "{market_list[0]}": 0.30,\n'
            f'   "{market_list[1]}": 0.25,\n'
            f'   "{market_list[2]}": 0.20,\n'
            '   "CASH": 0.25\n'
            " },\n"
            ' "reasoning": "brief explanation"\n'
            "}\n\n"
            "IMPORTANT RULES:\n"
            "1. Return ONLY the JSON object\n"
            "2. All allocations must sum to exactly 1.0 (100%)\n"
            "3. CASH allocation should reflect market conditions and risk tolerance\n"
            "4. Use double quotes for strings\n"
            "5. No trailing commas\n"
            "6. No additional text before or after the JSON"
        )


def create_polymarket_agent(
    name: str, model_name: str = "gpt-4o-mini"
) -> LLMPolyMarketAgent:
    return LLMPolyMarketAgent(name, model_name)

from __future__ import annotations

from typing import Any, Dict, Optional

from ..accounts import PolymarketAccount
from .base_agent import BaseAgent


class LLMPolyMarketAgent(BaseAgent[PolymarketAccount, Dict[str, Any]]):
    """Active polymarket portfolio manager using AI agents."""

    def __init__(self, name: str, model_name: str = "gpt-4o-mini") -> None:
        super().__init__(name, model_name)

    def _prepare_market_analysis(self, market_data: Dict[str, Dict[str, Any]]) -> str:
        """Prepare comprehensive market analysis for all markets."""
        analysis_parts = []

        for market_id, data in market_data.items():
            price = data.get("price", 0.0)
            question = data.get("question", market_id)
            category = data.get("category", "Unknown")
            yes_price = data.get("yes_price", price)
            no_price = data.get("no_price", 1.0 - yes_price)

            # Get price history
            prev = self.prev_price(market_id)
            pct = 0.0 if prev is None else ((price - prev) / prev) * 100.0
            trend = "up" if pct > 0 else ("down" if pct < 0 else "flat")
            hist = ", ".join(f"{p:.3f}" for p in self.history_tail(market_id, 3))

            analysis_parts.append(
                f"{market_id}: {question[:50]}... | YES: {yes_price:.3f} NO: {no_price:.3f} | {pct:+.2f}% ({trend}) | Category: {category} | History: [{hist}]"
            )

            # Update price history
            self._history.setdefault(market_id, []).append(price)
            if len(self._history[market_id]) > self.max_history:
                self._history[market_id] = self._history[market_id][-self.max_history :]
            self._last_price[market_id] = price

        return "MARKET ANALYSIS:\n" + "\n".join(analysis_parts)

    def _create_news_query(self, market_id: str, data: Dict[str, Any]) -> str:
        """Create polymarket-specific news query."""
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
        """Create complete portfolio allocation from LLM response."""
        allocations = parsed.get("allocations", {})

        if not allocations:
            print("⚠️ No allocations found in LLM response")
            return None

        # Validate that allocations sum to approximately 1.0
        total_allocation = sum(allocations.values())
        if abs(total_allocation - 1.0) > 0.1:  # Allow 10% tolerance
            print(
                f"⚠️ Allocations don't sum to 1.0 (got {total_allocation:.3f}), normalizing"
            )
            # Normalize allocations
            allocations = {k: v / total_allocation for k, v in allocations.items()}

        # Validate individual allocations
        for market_id, allocation in allocations.items():
            if not (0.0 <= allocation <= 1.0):
                print(
                    f"⚠️ Invalid allocation {allocation} for {market_id}, clamping to [0,1]"
                )
                allocations[market_id] = max(0.0, min(1.0, allocation))

        return allocations

    def _get_portfolio_prompt(self, analysis: str, market_data: Dict[str, Dict[str, Any]]) -> str:
        """Get portfolio allocation prompt for all markets."""
        market_list = list(market_data.keys())
        
        return (
            "You are a professional prediction market portfolio manager. Analyze the market data and generate a complete portfolio allocation.\n\n"
            f"Market Analysis:\n{analysis}\n\n"
            "PORTFOLIO MANAGEMENT PRINCIPLES:\n"
            "- Diversify across different market categories\n"
            "- Consider market sentiment and probability estimates\n"
            "- Balance high-confidence and speculative positions\n"
            "- Maintain appropriate position sizes\n"
            "- Total allocation must equal 100% (1.0)\n\n"
            f"AVAILABLE MARKETS: {market_list}\n\n"
            "CRITICAL: You must return ONLY valid JSON format. No additional text, explanations, or formatting.\n\n"
            "REQUIRED JSON FORMAT:\n"
            "{\n"
            ' "allocations": {\n'
            f'   "{market_list[0]}": 0.4,\n'
            f'   "{market_list[1]}": 0.3,\n'
            f'   "{market_list[2]}": 0.3\n'
            ' },\n'
            ' "reasoning": "brief explanation"\n'
            "}\n\n"
            "IMPORTANT RULES:\n"
            "1. Return ONLY the JSON object\n"
            "2. All allocations must sum to exactly 1.0\n"
            "3. Use double quotes for strings\n"
            "4. No trailing commas\n"
            "5. No additional text before or after the JSON"
        )


def create_polymarket_agent(
    name: str, model_name: str = "gpt-4o-mini"
) -> LLMPolyMarketAgent:
    """Create a new polymarket portfolio manager."""
    return LLMPolyMarketAgent(name, model_name)

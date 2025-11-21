"""
LLM agent specialized for forex portfolio allocation.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..accounts import ForexAccount
from .base_agent import BaseAgent


class LLMForexAgent(BaseAgent[ForexAccount, Dict[str, Any]]):
    """LLM-powered trading agent for major currency pairs."""

    def __init__(self, name: str, model_name: str = "gpt-4o-mini") -> None:
        super().__init__(name, model_name)

    def _prepare_market_analysis(self, market_data: Dict[str, Dict[str, Any]]) -> str:
        parts = []
        for pair, data in market_data.items():
            price = data.get("current_price", 0.0)
            base = data.get("base", pair[:3])
            quote = data.get("quote", pair[3:6])
            parts.append(f"{base}/{quote}: {price:.5f}")

            price_history = data.get("price_history", [])
            history_lines = self._format_price_history(
                price_history, pair, is_stock=False
            )
            parts.extend(history_lines)
            parts.append("")
            self._update_price_history(pair, price)

        return "FOREX MARKET ANALYSIS:\n" + "\n".join(parts)

    def _create_news_query(self, pair: str, data: Dict[str, Any]) -> str:
        base = data.get("base", pair[:3])
        quote = data.get("quote", pair[3:6])
        return f"{base} {quote} forex news"

    def _get_portfolio_prompt(
        self,
        analysis: str,
        market_data: Dict[str, Dict[str, Any]],
        date: Optional[str] = None,
    ) -> str:
        current_date_str = f"Today is {date} (UTC)." if date else ""
        pair_list = list(market_data.keys())
        pair_str = ", ".join(pair_list)
        sample = [
            pair_list[i] if i < len(pair_list) else f"PAIR_{i+1}"
            for i in range(3)
        ]

        return (
            f"{current_date_str}\n\n"
            "You are an institutional FX portfolio manager allocating capital across liquid G10 pairs. "
            "Use the market analysis, news context, and historical allocations to produce a diversified portfolio.\n\n"
            f"{analysis}\n\n"
            "OBJECTIVE:\n"
            "- Generate allocations for the next 1-3 weeks with focus on macro catalysts, rate differentials, and risk sentiment.\n"
            "- Maintain disciplined risk, prefer liquid pairs, and keep allocations sum to 1.0 (CASH allowed).\n"
            "- Balance trend-following with mean reversion when momentum is stretched.\n\n"
            "EVALUATION CRITERIA:\n"
            "- Consider rate expectations, macro data, and dollar strength.\n"
            "- Account for volatility and correlation across pairs.\n"
            "- Preserve capital during risk-off periods by raising CASH.\n"
            "- Highlight conviction trades clearly in the reasoning.\n\n"
            "REQUIRED JSON FORMAT:\n"
            "{\n"
            ' "reasoning": "Why this allocation makes sense for FX right now",\n'
            ' "allocations": {\n'
            f'   "{sample[0]}": 0.25,\n'
            f'   "{sample[1]}": 0.25,\n'
            f'   "{sample[2]}": 0.25,\n'
            '   "CASH": 0.25\n'
            " }\n"
            "}\n\n"
            "RULES:\n"
            "1. Return ONLY JSON (no prose outside the object).\n"
            "2. All allocations must be floats between 0 and 1 that sum to 1.\n"
            "3. CASH is optional but recommended in high-vol environments.\n"
            "4. Incorporate macro fundamentals, technicals, and positioning.\n"
            "5. Use double quotes for all keys/strings; no trailing commas.\n\n"
            f"AVAILABLE PAIRS: {pair_str}, CASH"
        )


def create_forex_agent(name: str, model_name: str = "gpt-4o-mini") -> LLMForexAgent:
    return LLMForexAgent(name, model_name)


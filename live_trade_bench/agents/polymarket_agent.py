from __future__ import annotations

from typing import Any, Dict, Optional

from ..accounts import PolymarketAccount
from .base_agent import BaseAgent


class LLMPolyMarketAgent(BaseAgent[PolymarketAccount, Dict[str, Any]]):
    def __init__(self, name: str, model_name: str = "gpt-4o-mini") -> None:
        super().__init__(name, model_name)

    def _prepare_market_analysis(self, market_data: Dict[str, Dict[str, Any]]) -> str:
        analysis_parts = []
        grouped_by_question: Dict[str, Dict[str, Any]] = {}

        for _, data in market_data.items():
            question = data["question"]
            grouped_by_question.setdefault(question, {})
            grouped_by_question[question][data["outcome"]] = {
                "price": data["price"],
                "price_history": data.get("price_history", []),
            }

        for question, outcomes in grouped_by_question.items():
            yes_data = outcomes.get("Yes", {"price": 0.0, "price_history": []})
            no_data = outcomes.get("No", {"price": 0.0, "price_history": []})

            analysis_parts.append(f"Question: {question}")
            analysis_parts.append(
                f"  - Betting YES current price: {yes_data['price']:.3f}"
            )
            analysis_parts.append(
                f"  - Betting NO current price: {no_data['price']:.3f}"
            )

            analysis_parts.append("  - Betting YES History:")
            yes_lines = self._format_price_history(
                yes_data["price_history"], "", is_stock=False
            )
            analysis_parts.extend(yes_lines if yes_lines else ["    N/A"])

            analysis_parts.append("  - Betting NO History:")
            no_lines = self._format_price_history(
                no_data["price_history"], "", is_stock=False
            )
            analysis_parts.extend(no_lines if no_lines else ["    N/A"])

            analysis_parts.append("")

        return "MARKET ANALYSIS:\n" + "\n".join(analysis_parts)

    def _get_portfolio_prompt(
        self,
        analysis: str,
        market_data: Dict[str, Dict[str, Any]],
        date: Optional[str] = None,
    ) -> str:
        current_date_str = f"Today is {date} (UTC)." if date else ""
        asset_list = list(market_data.keys())
        asset_list_str = ", ".join(asset_list)

        if len(asset_list) >= 2:
            example_allocations = (
                f'   "{asset_list[0]}": 0.25,\n'
                f'   "{asset_list[3]}": 0.15,\n'
                '   "CASH": 0.60'
            )
        elif asset_list:
            example_allocations = f'   "{asset_list[0]}": 0.50,\n   "CASH": 0.50'
        else:
            example_allocations = '   "CASH": 1.0'

        return (
            f"{current_date_str}\n\n"
            "You are a professional prediction-market portfolio manager. "
            "Analyze the market data and generate a complete portfolio allocation.\n\n"
            f"{analysis}\n\n"
            "PORTFOLIO MANAGEMENT OBJECTIVE:\n"
            "- For each market, YES and NO are two assets. Allocate to only one at a time. CASH is also valid.\n"
            "- YES and NO prices represent public-implied probabilities.\n"
            "DECISION LOGIC:\n"
            "- Derive market probability p_mkt from price.\n"
            "- Use news and history to form your belief p.\n"
            "- Go LONG {question}_YES if p > p_mkt + costs.\n"
            "- Go LONG {question}_NO if p < p_mkt - costs.\n"
            "- Never allocate to both YES and NO for the same question.\n\n"
            "PORTFOLIO PRINCIPLES:\n"
            "- Diversify across markets.\n"
            "- No simultaneous YES and NO allocations.\n"
            "- Incorporate news and history in decisions.\n"
            "- Total allocation must equal 1.0.\n\n"
            f"AVAILABLE ASSETS: {asset_list_str}, CASH\n\n"
            "CRITICAL: Return ONLY valid JSON. No extra text.\n\n"
            "REQUIRED JSON FORMAT:\n"
            "{\n"
            ' "reasoning": "Brief explanation of the allocation",\n'
            ' "allocations": {\n'
            f"{example_allocations}\n"
            " }\n"
            "}\n\n"
            "RULES:\n"
            "1. Return ONLY the JSON object.\n"
            "2. Allocations must sum to 1.0.\n"
            "3. Only one side (YES or NO) per question may be non-zero.\n"
            "4. Use double quotes; no trailing commas.\n"
            "Your objective is to maximize portfolio return using past allocations and performance history."
        )


def create_polymarket_agent(
    name: str, model_name: str = "gpt-4o-mini"
) -> LLMPolyMarketAgent:
    return LLMPolyMarketAgent(name, model_name)

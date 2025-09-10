from __future__ import annotations

from typing import Any, Dict

from ..accounts import PolymarketAccount
from .base_agent import BaseAgent


class LLMPolyMarketAgent(BaseAgent[PolymarketAccount, Dict[str, Any]]):
    def __init__(self, name: str, model_name: str = "gpt-4o-mini") -> None:
        super().__init__(name, model_name)

    def _prepare_market_analysis(self, market_data: Dict[str, Dict[str, Any]]) -> str:
        analysis_parts = []
        # In this new structure, market_data keys are like "{question}_YES"
        # We need to group them by question for analysis.
        grouped_by_question = {}
        for key, data in market_data.items():
            question = data["question"]
            if question not in grouped_by_question:
                grouped_by_question[question] = {}
            grouped_by_question[question][data["outcome"]] = data["price"]

        for question, outcomes in grouped_by_question.items():
            yes_price = outcomes.get("YES", 0.0)
            no_price = outcomes.get("NO", 0.0)
            analysis_parts.append(
                f"Question: {question} | YES_PRICE: {yes_price:.3f}, NO_PRICE: {no_price:.3f}"
            )
        return "MARKET ANALYSIS:\n" + "\n".join(analysis_parts)

    def _get_portfolio_prompt(
        self, analysis: str, market_data: Dict[str, Dict[str, Any]]
    ) -> str:
        # market_data keys are already in the format "{question}_YES" or "{question}_NO"
        asset_list = list(market_data.keys())

        example_allocations = ""
        if len(asset_list) >= 2:
            example_allocations = (
                f'   "{asset_list[0]}": 0.25,\n'
                f'   "{asset_list[3]}": 0.15,\n'
                '   "CASH": 0.60'
            )
        elif asset_list:
            example_allocations = f'   "{asset_list[0]}": 0.50,\n' '   "CASH": 0.50'
        else:
            example_allocations = '   "CASH": 1.0'

        return (
            "You are a professional prediction market portfolio manager. Analyze the market data and generate a complete portfolio allocation.\n\n"
            f"Market Analysis:\n{analysis}\n\n"
            "PORTFOLIO MANAGEMENT PRINCIPLES:\n"
            "- Diversify across different market outcomes.\n"
            "- For each question, allocating to both YES and NO simultaneously is irrational and should be avoided.\n"
            "- Total allocation must equal 100% (1.0).\n"
            "- CASH is a valid asset.\n\n"
            f"AVAILABLE ASSETS: {asset_list} + CASH\n\n"
            "CRITICAL: Return ONLY valid JSON format.\n\n"
            "REQUIRED JSON FORMAT:\n"
            "{\n"
            ' "allocations": {\n'
            f"{example_allocations}\n"
            " },\n"
            ' "reasoning": "A brief explanation of the investment strategy."\n'
            "}\n\n"
            "RULES:\n"
            "1. Return ONLY the JSON object.\n"
            "2. All allocations must sum to exactly 1.0.\n"
            "3. Use double quotes for strings."
        )

    # No longer need to override get_allocations. It will use the base class method.


def create_polymarket_agent(
    name: str, model_name: str = "gpt-4o-mini"
) -> LLMPolyMarketAgent:
    return LLMPolyMarketAgent(name, model_name)

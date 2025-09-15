from __future__ import annotations

from typing import Any, Dict, Optional

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
            grouped_by_question[question][data["outcome"]] = {
                "price": data["price"],
                "price_history": data.get("price_history", []),
            }

        for question, outcomes in grouped_by_question.items():
            yes_data = outcomes.get("YES", {"price": 0.0, "price_history": []})
            no_data = outcomes.get("NO", {"price": 0.0, "price_history": []})

            yes_price = yes_data["price"]
            no_price = no_data["price"]
            yes_history = yes_data["price_history"]
            no_history = no_data["price_history"]

            # Format current prices
            analysis_parts.append(f"Question: {question}")
            analysis_parts.append(f"  - Betting YES current price: {yes_price:.3f}")
            analysis_parts.append(f"  - Betting NO current price: {no_price:.3f}")

            # Format 10-day history with relative days for YES
            analysis_parts.append("  - Betting YES History:")
            yes_history_lines = self._format_price_history(
                yes_history, "", is_stock=False
            )
            if yes_history_lines:
                analysis_parts.extend(yes_history_lines)
            else:
                analysis_parts.append("    N/A")

            # Format 10-day history with relative days for NO
            analysis_parts.append("  - Betting NO History:")
            no_history_lines = self._format_price_history(
                no_history, "", is_stock=False
            )
            if no_history_lines:
                analysis_parts.extend(no_history_lines)
            else:
                analysis_parts.append("    N/A")

            analysis_parts.append("")  # Empty line for separation
        return "MARKET ANALYSIS:\n" + "\n".join(analysis_parts)

    def _get_portfolio_prompt(
        self, analysis: str, market_data: Dict[str, Dict[str, Any]], date: Optional[str] = None
    ) -> str:
        
        current_time_str = f"Current time is {date}." if date else ""
        
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
            f"{current_time_str}\n\nYou are a professional prediction-market portfolio manager. Analyze the market data and generate a complete portfolio allocation.\n\n"
            f"{analysis}\n\n"
            "PORTFOLIO MANAGEMENT OBJECTIVE:\n"
            "- For each market, YES and NO are two assets. You can only allocate to one of them at a time. You can allocate to CASH as well.\n"
            "- The price of YES and NO represents the probability of the YES and NO outcomes, respectively judged by the public.\n"
            "DECISION LOGIC FOR YES/NO MARKETS:\n"
            "- Infer market-implied probability p_mkt from price. If the price of YES is 0.4, then 40% of the public believes the YES outcome will happen.\n"
            "- You need to consider based on the news and the price history to form your belief. If the news is positive, you should allocate more to YES. If the news is negative, you should allocate more to NO.\n"
            "- Go LONG {question}_YES when your belief p > p_mkt + costs; go LONG {question}_NO when p < p_mkt - costs.\n"
            "- Never allocate to both YES and NO for the same question at the same time.\n"
            "PORTFOLIO MANAGEMENT PRINCIPLES:\n"
            "- Diversify across different market outcomes.\n"
            "- For each question, allocating to both YES and NO simultaneously is irrational and must be avoided.\n"
            "- Incorporate news flow and market price history when forming beliefs.\n"
            "- Total allocation must equal 100% (1.0).\n"
            "- CASH is a valid asset.\n\n"
            f"AVAILABLE ASSETS: {asset_list} + CASH\n\n"
            "CRITICAL: Return ONLY valid JSON format. No additional text, explanations, or formatting.\n\n"
            "REQUIRED JSON FORMAT:\n"
            "{\n"
            ' "allocations": {\n'
            f"{example_allocations}\n"
            " },\n"
            ' "reasoning": "A brief explanation about why you made this allocation"\n'
            "}\n\n"
            "RULES:\n"
            "1. Return ONLY the JSON object.\n"
            "2. All allocations must sum to exactly 1.0.\n"
            "3. For any given question, at most one side (YES or NO) may have a non-zero allocation.\n"
            "4. Use double quotes for strings; no trailing commas.\n"
            "Your objective is to maximize the return rate of your portfolio. You need to think based on your previous allocation history and return rate history to make this allocation."
        )


def create_polymarket_agent(
    name: str, model_name: str = "gpt-4o-mini"
) -> LLMPolyMarketAgent:
    return LLMPolyMarketAgent(name, model_name)

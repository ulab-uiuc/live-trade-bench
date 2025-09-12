from __future__ import annotations

from typing import Any, Dict

from ..accounts import StockAccount
from .base_agent import BaseAgent


class LLMStockAgent(BaseAgent[StockAccount, Dict[str, Any]]):
    def __init__(self, name: str, model_name: str = "gpt-4o-mini") -> None:
        super().__init__(name, model_name)

    def _prepare_market_analysis(self, market_data: Dict[str, Dict[str, Any]]) -> str:
        analysis_parts = []
        for ticker, data in market_data.items():
            price = data.get("current_price", 0.0)
            price_history = data.get("price_history", [])
            
            # Format current price
            current_info = f"{ticker}: Current price is ${price:.2f}"
            analysis_parts.append(current_info)
            
            # Format 5-day history with relative days
            history_lines = self._format_price_history(price_history, ticker, is_stock=True)
            analysis_parts.extend(history_lines)
            
            analysis_parts.append("")  # Empty line for separation
            self._update_price_history(ticker, price)
        return "MARKET ANALYSIS:\n" + "\n".join(analysis_parts)

    def _create_news_query(self, ticker: str, data: Dict[str, Any]) -> str:
        return f"{ticker} stock earnings news"

    def _get_portfolio_prompt(
        self, analysis: str, market_data: Dict[str, Dict[str, Any]]
    ) -> str:
        stock_list = list(market_data.keys())
        return (
            "You are a professional portfolio manager. Analyze the market data and generate a complete portfolio allocation.\n\n"
            f"{analysis}\n\n"
            "PORTFOLIO MANAGEMENT PRINCIPLES:\n"
            "- Diversify across sectors and market caps\n"
            "- Consider market momentum and fundamentals\n"
            "- Balance growth and value opportunities\n"
            "- Maintain appropriate position sizes\n"
            "- Total allocation must equal 100% (1.0)\n"
            "- CASH is a valid asset that should be allocated based on market conditions\n\n"
            f"AVAILABLE ASSETS: {stock_list} + CASH\n\n"
            "CRITICAL: You must return ONLY valid JSON format. No additional text, explanations, or formatting.\n\n"
            "REQUIRED JSON FORMAT:\n"
            "{\n"
            ' "allocations": {\n'
            f'   "{stock_list[0]}": 0.25,\n'
            f'   "{stock_list[1]}": 0.20,\n'
            f'   "{stock_list[2]}": 0.15,\n'
            '   "CASH": 0.40\n'
            " },\n"
            ' "reasoning": "brief explanation about why you made this allocation"\n'
            "}\n\n"
            "IMPORTANT RULES:\n"
            "1. Return ONLY the JSON object\n"
            "2. All allocations must sum to exactly 1.0 (100%)\n"
            "3. CASH allocation should reflect market conditions and risk tolerance\n"
            "4. Use double quotes for strings\n"
            "5. No trailing commas\n"
            "6. No additional text before or after the JSON"
        )


def create_stock_agent(name: str, model_name: str = "gpt-4o-mini") -> LLMStockAgent:
    return LLMStockAgent(name, model_name)

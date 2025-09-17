from __future__ import annotations

from typing import Any, Dict, Optional

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

            analysis_parts.append(f"{ticker}: Current price is ${price:.2f}")

            history_lines = self._format_price_history(
                price_history, ticker, is_stock=True
            )
            analysis_parts.extend(history_lines)

            analysis_parts.append("")
            self._update_price_history(ticker, price)

        return "MARKET ANALYSIS:\n" + "\n".join(analysis_parts)

    def _create_news_query(self, ticker: str, data: Dict[str, Any]) -> str:
        return f"{ticker} stock news"

    def _get_portfolio_prompt(
        self,
        analysis: str,
        market_data: Dict[str, Dict[str, Any]],
        date: Optional[str] = None,
    ) -> str:
        current_date_str = f"Today is {date}." if date else ""
        stock_list = list(market_data.keys())
        stock_list_str = ", ".join(stock_list)
        sample = [
            stock_list[i] if i < len(stock_list) else f"ASSET_{i+1}" for i in range(3)
        ]

        return (
            f"{current_date_str}\n\n"
            "You are a professional portfolio manager. Analyze the market data and generate a complete portfolio allocation.\n\n"
            f"{analysis}\n\n"
            "PORTFOLIO MANAGEMENT OBJECTIVE:\n"
            "- Improve total returns by selecting allocations with higher expected return per unit of risk.\n"
            "- Aim to outperform a reasonable baseline (e.g., equal-weight of AVAILABLE ASSETS) over the next 1–3 months.\n"
            "- Use CASH tactically for capital protection in unfavorable markets.\n\n"
            "EVALUATION CRITERIA:\n"
            "- Prefer allocations that increase expected excess return and improve risk-adjusted return.\n"
            "- Maintain sector and factor diversification.\n"
            "- Be mindful of turnover and liquidity.\n\n"
            "PORTFOLIO PRINCIPLES:\n"
            "- Diversify across sectors and market caps.\n"
            "- Consider market momentum and fundamentals.\n"
            "- Balance growth and value opportunities.\n"
            "- Maintain appropriate position sizes.\n"
            "- Total allocation must equal 1.0.\n"
            "- CASH is a valid asset.\n\n"
            f"AVAILABLE ASSETS: {stock_list_str}, CASH\n\n"
            "CRITICAL: Return ONLY valid JSON. No extra text.\n\n"
            "REQUIRED JSON FORMAT:\n"
            "{\n"
            ' "reasoning": "Brief explanation about why this allocation improves return rate",\n'
            ' "allocations": {\n'
            f'   "{sample[0]}": 0.25,\n'
            f'   "{sample[1]}": 0.20,\n'
            f'   "{sample[2]}": 0.15,\n'
            '   "CASH": 0.40\n'
            " }\n"
            "}\n\n"
            "RULES:\n"
            "1. Return ONLY the JSON object.\n"
            "2. Allocations must sum to 1.0.\n"
            "3. CASH allocation should reflect market conditions.\n"
            "4. Use double quotes for strings.\n"
            "5. No trailing commas.\n"
            "6. No extra text outside the JSON.\n"
            "Your objective is to maximize return while considering previous allocations and performance history."
        )


def create_stock_agent(name: str, model_name: str = "gpt-4o-mini") -> LLMStockAgent:
    return LLMStockAgent(name, model_name)

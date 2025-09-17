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

            # Format current price
            current_info = f"{ticker}: Current price is ${price:.2f}"
            analysis_parts.append(current_info)

            # Format 10-day history with relative days
            history_lines = self._format_price_history(
                price_history, ticker, is_stock=True
            )
            analysis_parts.extend(history_lines)

            analysis_parts.append("")  # Empty line for separation
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
            f"{current_date_str}\n\nYou are a professional portfolio manager. Analyze the market data and generate a complete portfolio allocation.\n\n"
            f"{analysis}\n\n"
            "PORTFOLIO MANAGEMENT OBJECTIVE:\n"
            "- Primary goal: improve total returns by selecting allocations with higher expected return per unit of risk (risk-adjusted return), net of trading costs.\n"
            "- Aim to outperform a reasonable baseline (e.g., equal-weight of AVAILABLE ASSETS) over the next 1–3 months while keeping drawdowns and volatility contained.\n"
            "- Treat CASH as a tactical asset for capital protection when market conditions are unfavorable.\n\n"
            "EVALUATION CRITERIA FOR THIS OBJECTIVE:\n"
            "- Prefer allocations that increase expected excess return and improve risk-adjusted return (Sharpe-like reasoning) given the analysis.\n"
            "- Keep portfolio concentration reasonable; maintain sector and factor diversification.\n"
            "- Be mindful of turnover and liquidity (avoid excessive trading for marginal benefit).\n\n"
            "PORTFOLIO MANAGEMENT PRINCIPLES:\n"
            "- Diversify across sectors and market caps\n"
            "- Consider market momentum and fundamentals\n"
            "- Balance growth and value opportunities\n"
            "- Maintain appropriate position sizes\n"
            "- Total allocation must equal 100% (1.0)\n"
            "- CASH is a valid asset that should be allocated based on market conditions\n\n"
            f"AVAILABLE ASSETS: {stock_list_str}, CASH\n\n"
            "CRITICAL: You must return ONLY valid JSON format. No additional text, explanations, or formatting.\n\n"
            "REQUIRED JSON FORMAT:\n"
            "{\n"
            ' "reasoning": "brief explanation about why you think this allocation is better than the previous allocation to make higher return rate",\n'
            ' "allocations": {\n'
            f'   "{sample[0]}": 0.25,\n'
            f'   "{sample[1]}": 0.20,\n'
            f'   "{sample[2]}": 0.15,\n'
            '   "CASH": 0.40\n'
            " }\n"
            "}\n\n"
            "IMPORTANT RULES:\n"
            "1. Return ONLY the JSON object\n"
            "2. All allocations must sum to exactly 1.0 (100%)\n"
            "3. CASH allocation should reflect market conditions and risk tolerance\n"
            "4. Use double quotes for strings\n"
            "5. No trailing commas\n"
            "6. No additional text before or after the JSON\n"
            "Your objective is to maximize the return rate of your portfolio. You need to think based on your previous allocation history and return rate history to make this allocation."
        )


def create_stock_agent(name: str, model_name: str = "gpt-4o-mini") -> LLMStockAgent:
    return LLMStockAgent(name, model_name)

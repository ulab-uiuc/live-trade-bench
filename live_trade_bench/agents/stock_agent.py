from __future__ import annotations

from typing import Any, Dict, Optional

from ..accounts import StockAccount
from .base_agent import BaseAgent


class LLMStockAgent(BaseAgent[StockAccount, Dict[str, Any]]):
    """Active stock portfolio manager using AI agents."""

    def __init__(self, name: str, model_name: str = "gpt-4o-mini") -> None:
        super().__init__(name, model_name)

    def _prepare_market_analysis(self, market_data: Dict[str, Dict[str, Any]]) -> str:
        """Prepare comprehensive market analysis for all stocks."""
        analysis_parts = []

        for ticker, data in market_data.items():
            price = data.get("current_price", 0.0)
            name = data.get("name", ticker)
            sector = data.get("sector", "Unknown")

            analysis_parts.append(f"{ticker} ({name}): ${price:.2f} | Sector: {sector}")

        return "MARKET ANALYSIS:\n" + "\n".join(analysis_parts)

    def _create_news_query(self, ticker: str, data: Dict[str, Any]) -> str:
        """Create stock-specific news query."""
        return f"{ticker} stock earnings news"

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
        for ticker, allocation in allocations.items():
            if not (0.0 <= allocation <= 1.0):
                print(
                    f"⚠️ Invalid allocation {allocation} for {ticker}, clamping to [0,1]"
                )
                allocations[ticker] = max(0.0, min(1.0, allocation))

        return allocations

    def _get_portfolio_prompt(
        self, analysis: str, market_data: Dict[str, Dict[str, Any]]
    ) -> str:
        """Get portfolio allocation prompt for all stocks."""
        stock_list = list(market_data.keys())

        return (
            "You are a professional portfolio manager. Analyze the market data and generate a complete portfolio allocation.\n\n"
            f"Market Analysis:\n{analysis}\n\n"
            "PORTFOLIO MANAGEMENT PRINCIPLES:\n"
            "- Diversify across sectors and market caps\n"
            "- Consider market momentum and fundamentals\n"
            "- Balance growth and value opportunities\n"
            "- Maintain appropriate position sizes\n"
            "- Total allocation must equal 100% (1.0)\n\n"
            f"AVAILABLE STOCKS: {stock_list}\n\n"
            "CRITICAL: You must return ONLY valid JSON format. No additional text, explanations, or formatting.\n\n"
            "REQUIRED JSON FORMAT:\n"
            "{\n"
            ' "allocations": {\n'
            f'   "{stock_list[0]}": 0.3,\n'
            f'   "{stock_list[1]}": 0.3,\n'
            f'   "{stock_list[2]}": 0.4\n'
            " },\n"
            ' "reasoning": "brief explanation"\n'
            "}\n\n"
            "IMPORTANT RULES:\n"
            "1. Return ONLY the JSON object\n"
            "2. All allocations must sum to exactly 1.0\n"
            "3. Use double quotes for strings\n"
            "4. No trailing commas\n"
            "5. No additional text before or after the JSON"
        )


def create_stock_agent(name: str, model_name: str = "gpt-4o-mini") -> LLMStockAgent:
    """Create a new stock portfolio manager."""
    return LLMStockAgent(name, model_name)

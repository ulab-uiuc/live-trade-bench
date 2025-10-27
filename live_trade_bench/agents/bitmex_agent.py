"""
BitMEX LLM Agent for crypto perpetual contract trading.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..accounts import BitMEXAccount
from .base_agent import BaseAgent


class LLMBitMEXAgent(BaseAgent[BitMEXAccount, Dict[str, Any]]):
    """LLM-powered trading agent for BitMEX perpetual contracts."""

    def __init__(self, name: str, model_name: str = "gpt-4o-mini") -> None:
        super().__init__(name, model_name)

    def _prepare_market_analysis(self, market_data: Dict[str, Dict[str, Any]]) -> str:
        """
        Prepare market analysis for BitMEX perpetual contracts.

        Includes crypto-specific data:
        - BTC/USD price formatting
        - Funding rates
        - Order book depth
        - Open interest
        """
        analysis_parts = []

        for symbol, data in market_data.items():
            price = data.get("current_price", 0.0)
            price_history = data.get("price_history", [])

            # Format price with crypto-specific styling
            if "USD" in symbol or "USDT" in symbol:
                analysis_parts.append(f"{symbol}: Current price is ${price:,.2f}")
            else:
                analysis_parts.append(f"{symbol}: Current price is {price:.6f}")

            # Add funding rate if available
            funding_rate = data.get("funding_rate")
            if funding_rate is not None:
                funding_pct = funding_rate * 100
                analysis_parts.append(f"  - Funding rate: {funding_pct:.4f}%")

            # Add order book depth if available
            bid_depth = data.get("bid_depth")
            ask_depth = data.get("ask_depth")
            if bid_depth and ask_depth:
                analysis_parts.append(
                    f"  - Order book: Bid depth ${bid_depth:,.0f} | Ask depth ${ask_depth:,.0f}"
                )

            # Add open interest if available
            open_interest = data.get("open_interest")
            if open_interest:
                analysis_parts.append(f"  - Open interest: {open_interest:,.0f} contracts")

            # Price history
            history_lines = self._format_price_history(
                price_history, symbol, is_stock=False
            )
            analysis_parts.extend(history_lines)

            analysis_parts.append("")
            self._update_price_history(symbol, price)

        return "MARKET ANALYSIS:\n" + "\n".join(analysis_parts)

    def _create_news_query(self, ticker: str, data: Dict[str, Any]) -> str:
        """
        Create crypto-specific news query.

        Maps contract symbols to readable cryptocurrency names.
        """
        # Map common BitMEX symbols to crypto names
        symbol_map = {
            "XBTUSD": "Bitcoin",
            "XBTUSDT": "Bitcoin",
            "ETHUSD": "Ethereum",
            "ETHUSDT": "Ethereum",
            "SOLUSDT": "Solana",
            "BNBUSDT": "BNB Binance",
            "XRPUSDT": "XRP Ripple",
            "ADAUSDT": "Cardano",
            "DOGEUSDT": "Dogecoin",
            "AVAXUSDT": "Avalanche",
            "LINKUSDT": "Chainlink",
            "LTCUSDT": "Litecoin",
        }

        crypto_name = symbol_map.get(ticker, ticker)
        return f"{crypto_name} crypto news"

    def _get_portfolio_prompt(
        self,
        analysis: str,
        market_data: Dict[str, Dict[str, Any]],
        date: Optional[str] = None,
    ) -> str:
        """
        Generate LLM prompt for BitMEX portfolio allocation.

        Includes crypto-specific considerations:
        - 24/7 market volatility
        - Funding rate carry costs
        - Market liquidity from order book depth
        """
        current_date_str = f"Today is {date} (UTC)." if date else ""
        contract_list = list(market_data.keys())
        contract_list_str = ", ".join(contract_list)
        sample = [
            contract_list[i] if i < len(contract_list) else f"CONTRACT_{i+1}"
            for i in range(3)
        ]

        return (
            f"{current_date_str}\n\n"
            "You are a professional crypto derivatives trader managing a perpetual contract portfolio on BitMEX. "
            "Analyze the market data and generate a complete portfolio allocation.\n\n"
            f"{analysis}\n\n"
            "PORTFOLIO MANAGEMENT OBJECTIVE:\n"
            "- Maximize returns by selecting contracts with favorable risk/reward profiles.\n"
            "- Consider funding rates as they affect carry costs (paid every 8 hours).\n"
            "- Outperform equal-weight baseline over 1-2 week timeframes.\n"
            "- Use CASH tactically during adverse market conditions.\n\n"
            "CRYPTO MARKET CONSIDERATIONS:\n"
            "- Markets trade 24/7 with high volatility.\n"
            "- Funding rates create carry costs/profits (positive rate = longs pay shorts).\n"
            "- Order book depth indicates liquidity and slippage risk.\n"
            "- Open interest shows market positioning and potential squeeze points.\n"
            "- Correlation risk: many crypto assets move together.\n\n"
            "EVALUATION CRITERIA:\n"
            "- Prefer contracts with positive expected returns after funding costs.\n"
            "- Consider momentum, volatility, and liquidity.\n"
            "- Diversify across different crypto assets when possible.\n"
            "- Monitor funding rates for carry trade opportunities.\n\n"
            "PORTFOLIO PRINCIPLES:\n"
            "- Diversify across major cryptocurrencies when favorable.\n"
            "- Consider market momentum and technical patterns.\n"
            "- Balance between high-beta and stable contracts.\n"
            "- Account for funding rate impacts on carry.\n"
            "- Total allocation must equal 1.0.\n"
            "- CASH is a valid asset for capital preservation.\n\n"
            f"AVAILABLE CONTRACTS: {contract_list_str}, CASH\n\n"
            "CRITICAL: Return ONLY valid JSON. No extra text.\n\n"
            "REQUIRED JSON FORMAT:\n"
            "{\n"
            ' "reasoning": "Brief explanation of allocation strategy considering funding rates and market conditions",\n'
            ' "allocations": {\n'
            f'   "{sample[0]}": 0.30,\n'
            f'   "{sample[1]}": 0.25,\n'
            f'   "{sample[2]}": 0.20,\n'
            '   "CASH": 0.25\n'
            " }\n"
            "}\n\n"
            "RULES:\n"
            "1. Return ONLY the JSON object.\n"
            "2. Allocations must sum to 1.0.\n"
            "3. Consider funding rates when allocating.\n"
            "4. CASH allocation should reflect crypto market risk.\n"
            "5. Use double quotes for strings.\n"
            "6. No trailing commas.\n"
            "7. No extra text outside the JSON.\n"
            "Your objective is to maximize returns while managing crypto-specific risks including funding costs and 24/7 volatility."
        )


def create_bitmex_agent(
    name: str, model_name: str = "gpt-4o-mini"
) -> LLMBitMEXAgent:
    """
    Create a new BitMEX trading agent.

    Args:
        name: Agent display name
        model_name: LLM model identifier

    Returns:
        Initialized LLMBitMEXAgent instance
    """
    return LLMBitMEXAgent(name, model_name)

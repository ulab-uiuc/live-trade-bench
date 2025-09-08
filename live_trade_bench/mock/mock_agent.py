"""
Mock Agents - Generate fake but realistic portfolio decisions for testing
"""

import random
from typing import Any, Dict, List, Optional

from ..agents.base_agent import BaseAgent


class MockBaseAgent(BaseAgent[Any, Dict[str, Any]]):
    """Mock base agent that eliminates LLM calls and generates deterministic allocations"""

    def __init__(self, name: str, model_name: str = "mock-model") -> None:
        super().__init__(name, model_name)

    def _call_llm(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Mock LLM call - always returns success with fake JSON response"""
        return {
            "success": True,
            "content": self._generate_mock_llm_response(messages),
            "error": None,
        }

    def _generate_mock_llm_response(self, messages: List[Dict[str, str]]) -> str:
        """Generate fake LLM JSON response based on prompt analysis"""
        # This will be overridden by subclasses to provide domain-specific responses
        return '{"allocations": {"CASH": 1.0}, "reasoning": "Mock response"}'


class MockStockAgent(MockBaseAgent):
    """Mock stock agent generating fake but realistic stock portfolio decisions"""

    def __init__(self, name: str, model_name: str = "mock-stock-model") -> None:
        super().__init__(name, model_name)

    def _prepare_market_analysis(self, market_data: Dict[str, Dict[str, Any]]) -> str:
        """Generate mock market analysis matching real StockAgent format"""
        analysis_parts = []
        for ticker, data in market_data.items():
            price = data.get("current_price", 100.0)
            name = data.get("name", ticker)
            sector = data.get("sector", "Technology")

            # Generate mock price movement
            prev = self.prev_price(ticker)
            if prev is None:
                # First time seeing this ticker, simulate reasonable previous price
                prev = price * random.uniform(0.95, 1.05)

            pct = ((price - prev) / prev) * 100.0
            trend = "up" if pct > 0 else ("down" if pct < 0 else "flat")

            # Generate mock history
            hist = ", ".join(
                f"{price * random.uniform(0.98, 1.02):.2f}"
                for _ in range(min(3, len(self.history_tail(ticker, 3)) + 1))
            )

            analysis_parts.append(
                f"{ticker} ({name}): ${price:.2f} | {pct:+.2f}% ({trend}) | Sector: {sector} | History: [{hist}]"
            )
            self._update_price_history(ticker, price)

        return "MARKET ANALYSIS:\n" + "\n".join(analysis_parts)

    def _create_news_query(self, ticker: str, data: Dict[str, Any]) -> str:
        """Generate mock news query"""
        return f"{ticker} stock earnings news"

    def _generate_mock_llm_response(self, messages: List[Dict[str, str]]) -> str:
        """Generate mock stock portfolio allocation"""
        # Extract available tickers from the prompt
        prompt = messages[0]["content"] if messages else ""

        # Simple parsing to find AVAILABLE ASSETS
        tickers = []
        if "AVAILABLE ASSETS:" in prompt:
            assets_line = prompt.split("AVAILABLE ASSETS:")[1].split("\n")[0]
            # Remove "CASH" and clean up
            assets_str = assets_line.replace("+ CASH", "").strip()
            if "[" in assets_str and "]" in assets_str:
                assets_str = assets_str.strip("[]")
            tickers = [
                t.strip().strip("'\"")
                for t in assets_str.split(",")
                if t.strip() and "CASH" not in t
            ]

        if not tickers:
            # Fallback to common stocks if parsing failed
            tickers = ["AAPL", "MSFT", "GOOGL"]

        # Generate realistic allocations
        allocations = {}

        # Randomly select 2-4 stocks to invest in
        selected_tickers = random.sample(
            tickers, min(len(tickers), random.randint(2, 4))
        )

        # Generate weights that sum to less than 1.0 (rest goes to CASH)
        total_equity_allocation = random.uniform(0.6, 0.9)  # 60-90% in stocks

        # Distribute among selected stocks
        weights = [random.random() for _ in selected_tickers]
        weight_sum = sum(weights)

        for i, ticker in enumerate(selected_tickers):
            allocations[ticker] = round(
                (weights[i] / weight_sum) * total_equity_allocation, 3
            )

        # CASH gets the remainder
        allocations["CASH"] = round(1.0 - sum(allocations.values()), 3)

        # Ensure exact sum to 1.0
        total = sum(allocations.values())
        if abs(total - 1.0) > 0.001:
            allocations["CASH"] = round(allocations["CASH"] + (1.0 - total), 3)

        reasoning = f"Mock allocation: {len(selected_tickers)} stocks ({total_equity_allocation*100:.0f}% equity)"

        response = {"allocations": allocations, "reasoning": reasoning}

        import json

        return json.dumps(response)

    def _create_portfolio_allocation_from_response(
        self, parsed: Dict[str, Any], market_data: Dict[str, Dict[str, Any]]
    ) -> Optional[Dict[str, float]]:
        """Create portfolio allocation from mock response"""
        normalized = self._normalize_allocations_from_parsed(parsed)
        if not normalized:
            print("� No allocations found in mock response")
            return None
        return normalized

    def _get_portfolio_prompt(
        self, analysis: str, market_data: Dict[str, Dict[str, Any]]
    ) -> str:
        """Generate portfolio prompt (used by mock LLM response generation)"""
        stock_list = list(market_data.keys())
        return (
            "You are a professional portfolio manager. Analyze the market data and generate a complete portfolio allocation.\n\n"
            f"Market Analysis:\n{analysis}\n\n"
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
            f'   "{stock_list[0] if stock_list else "AAPL"}": 0.25,\n'
            f'   "{stock_list[1] if len(stock_list) > 1 else "MSFT"}": 0.20,\n'
            f'   "{stock_list[2] if len(stock_list) > 2 else "GOOGL"}": 0.15,\n'
            '   "CASH": 0.40\n'
            " },\n"
            ' "reasoning": "brief explanation"\n'
            "}\n\n"
            "IMPORTANT RULES:\n"
            "1. Return ONLY the JSON object\n"
            "2. All allocations must sum to exactly 1.0 (100%)\n"
            "3. CASH allocation should reflect market conditions and risk tolerance\n"
            "4. Use double quotes for strings\n"
            "5. No trailing commas\n"
            "6. No additional text before or after the JSON"
        )


class MockPolymarketAgent(MockBaseAgent):
    """Mock polymarket agent generating fake but realistic prediction market decisions"""

    def __init__(self, name: str, model_name: str = "mock-polymarket-model") -> None:
        super().__init__(name, model_name)

    def _prepare_market_analysis(self, market_data: Dict[str, Dict[str, Any]]) -> str:
        """Generate mock polymarket analysis matching real PolymarketAgent format"""
        analysis_parts = []
        for market_id, data in market_data.items():
            price = data.get("price", 0.5)
            question = data.get("question", f"Mock question for {market_id}")
            category = data.get("category", "Politics")
            yes_price = data.get("yes_price", price)
            no_price = data.get("no_price", 1.0 - yes_price)

            # Generate mock price movement
            prev = self.prev_price(market_id)
            if prev is None:
                prev = price * random.uniform(0.9, 1.1)

            pct = ((price - prev) / prev) * 100.0 if prev > 0 else 0.0
            trend = "up" if pct > 0 else ("down" if pct < 0 else "flat")

            # Generate mock history
            hist = ", ".join(
                f"{price * random.uniform(0.95, 1.05):.3f}"
                for _ in range(min(3, len(self.history_tail(market_id, 3)) + 1))
            )

            analysis_parts.append(
                f"{market_id}: {question[:50]}... | YES: {yes_price:.3f} NO: {no_price:.3f} | {pct:+.2f}% ({trend}) | Category: {category} | History: [{hist}]"
            )
            self._update_price_history(market_id, price)

        return "MARKET ANALYSIS:\n" + "\n".join(analysis_parts)

    def _create_news_query(self, market_id: str, data: Dict[str, Any]) -> str:
        """Generate mock news query for prediction market"""
        question = data.get("question", "")
        category = data.get("category", "")
        if question and len(question) > 10:
            key_terms = question.split()[:5]
            return " ".join(key_terms)
        elif category:
            return f"{category} prediction market"
        else:
            return f"polymarket {market_id}"

    def _generate_mock_llm_response(self, messages: List[Dict[str, str]]) -> str:
        """Generate mock polymarket portfolio allocation"""
        # Extract available markets from the prompt
        prompt = messages[0]["content"] if messages else ""

        # Simple parsing to find AVAILABLE ASSETS
        markets = []
        if "AVAILABLE ASSETS:" in prompt:
            assets_line = prompt.split("AVAILABLE ASSETS:")[1].split("\n")[0]
            # Remove "CASH" and clean up
            assets_str = assets_line.replace("+ CASH", "").strip()
            if "[" in assets_str and "]" in assets_str:
                assets_str = assets_str.strip("[]")
            markets = [
                m.strip().strip("'\"")
                for m in assets_str.split(",")
                if m.strip() and "CASH" not in m
            ]

        if not markets:
            # Fallback to mock markets if parsing failed
            markets = ["market_1", "market_2", "market_3"]

        # Generate realistic allocations for prediction markets
        allocations = {}

        # Randomly select 1-3 markets to invest in (more focused than stocks)
        selected_markets = random.sample(
            markets, min(len(markets), random.randint(1, 3))
        )

        # Generate weights that sum to less than 1.0 (rest goes to CASH)
        total_market_allocation = random.uniform(
            0.4, 0.8
        )  # 40-80% in markets (more conservative)

        # Distribute among selected markets
        weights = [random.random() for _ in selected_markets]
        weight_sum = sum(weights)

        for i, market in enumerate(selected_markets):
            allocations[market] = round(
                (weights[i] / weight_sum) * total_market_allocation, 3
            )

        # CASH gets the remainder
        allocations["CASH"] = round(1.0 - sum(allocations.values()), 3)

        # Ensure exact sum to 1.0
        total = sum(allocations.values())
        if abs(total - 1.0) > 0.001:
            allocations["CASH"] = round(allocations["CASH"] + (1.0 - total), 3)

        reasoning = f"Mock allocation: {len(selected_markets)} markets ({total_market_allocation*100:.0f}% prediction markets)"

        response = {"allocations": allocations, "reasoning": reasoning}

        import json

        return json.dumps(response)

    def _create_portfolio_allocation_from_response(
        self, parsed: Dict[str, Any], market_data: Dict[str, Dict[str, Any]]
    ) -> Optional[Dict[str, float]]:
        """Create portfolio allocation from mock response"""
        normalized = self._normalize_allocations_from_parsed(parsed)
        if not normalized:
            print("� No allocations found in mock response")
            return None
        return normalized

    def _get_portfolio_prompt(
        self, analysis: str, market_data: Dict[str, Dict[str, Any]]
    ) -> str:
        """Generate portfolio prompt (used by mock LLM response generation)"""
        market_list = list(market_data.keys())
        return (
            "You are a professional prediction market portfolio manager. Analyze the market data and generate a complete portfolio allocation.\n\n"
            f"Market Analysis:\n{analysis}\n\n"
            "PORTFOLIO MANAGEMENT PRINCIPLES:\n"
            "- Diversify across different market categories\n"
            "- Consider market sentiment and probability estimates\n"
            "- Balance high-confidence and speculative positions\n"
            "- Maintain appropriate position sizes\n"
            "- Total allocation must equal 100% (1.0)\n"
            "- CASH is a valid asset that should be allocated based on market conditions\n\n"
            f"AVAILABLE ASSETS: {market_list} + CASH\n\n"
            "CRITICAL: You must return ONLY valid JSON format. No additional text, explanations, or formatting.\n\n"
            "REQUIRED JSON FORMAT:\n"
            "{\n"
            ' "allocations": {\n'
            f'   "{market_list[0] if market_list else "market_1"}": 0.30,\n'
            f'   "{market_list[1] if len(market_list) > 1 else "market_2"}": 0.25,\n'
            f'   "{market_list[2] if len(market_list) > 2 else "market_3"}": 0.20,\n'
            '   "CASH": 0.25\n'
            " },\n"
            ' "reasoning": "brief explanation"\n'
            "}\n\n"
            "IMPORTANT RULES:\n"
            "1. Return ONLY the JSON object\n"
            "2. All allocations must sum to exactly 1.0 (100%)\n"
            "3. CASH allocation should reflect market conditions and risk tolerance\n"
            "4. Use double quotes for strings\n"
            "5. No trailing commas\n"
            "6. No additional text before or after the JSON"
        )


# Export convenience functions matching real agents
def create_mock_stock_agent(
    name: str, model_name: str = "mock-stock-model"
) -> MockStockAgent:
    """Create a mock stock agent for testing"""
    return MockStockAgent(name, model_name)


def create_mock_polymarket_agent(
    name: str, model_name: str = "mock-polymarket-model"
) -> MockPolymarketAgent:
    """Create a mock polymarket agent for testing"""
    return MockPolymarketAgent(name, model_name)

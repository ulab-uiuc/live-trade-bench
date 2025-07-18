from typing import List, Dict, Any, Optional
from .single_stock_model import BaseModel
from trading_bench.utils.llm.openai_llm import OpenAILLMClient
import json
from datetime import datetime

class PortfolioModel(BaseModel):
    """
    AI-powered portfolio analysis model for multi-stock joint decision making.
    This model takes a pool of stocks, their price histories, and news,
    and asks an LLM to give a joint trading decision for the whole pool.
    """
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gpt-4", base_url: Optional[str] = None):
        self.llm = OpenAILLMClient(api_key=api_key, model_name=model_name, base_url=base_url)
        self.base_url = base_url or "https://api.openai.com/v1"
        self.model_name = model_name

    def _format_portfolio_prompt(
        self,
        tickers: List[str],
        price_histories: Dict[str, List[float]],
        news_data: Dict[str, List[Dict[str, Any]]],
        date: str,
        total_capital: float = None,
    ) -> str:
        """
        Format a prompt for the LLM that summarizes all stocks' price and news data.
        """
        prompt = f"""
        Portfolio Analysis Date: {date}
        """
        if total_capital:
            prompt += f"\nTotal Capital Available: ${total_capital:,.2f}\n"
        for ticker in tickers:
            prices = price_histories.get(ticker, [])
            if not prices:
                continue
            latest_price = prices[-1]
            ma_5 = sum(prices[-5:]) / min(5, len(prices))
            ma_10 = sum(prices[-10:]) / min(10, len(prices))
            ma_20 = sum(prices[-20:]) / min(20, len(prices))
            prompt += f"""
Stock: {ticker}
  Latest Price: ${latest_price:.2f}
  5-day MA: ${ma_5:.2f}
  10-day MA: ${ma_10:.2f}
  20-day MA: ${ma_20:.2f}
  Recent Prices: {prices[-10:]}
"""
            news_list = news_data.get(ticker, [])
            if news_list:
                prompt += f"  News Headlines ({len(news_list)}):\n"
                for i, article in enumerate(news_list[:3], 1):
                    prompt += f"    {i}. {article['title']} (Source: {article.get('source', 'Unknown')}, Date: {article.get('date', 'Unknown')})\n"
                if len(news_list) > 3:
                    prompt += f"    ...and {len(news_list) - 3} more articles.\n"
            else:
                prompt += "  No recent news.\n"
        prompt += """

You are a portfolio trading strategist. Based on the above data, recommend for each stock:
- action: 'buy', 'sell', or 'hold'
- weight: allocation proportion (0-1, sum <= 1 if total_capital is given)
- confidence: float between 0.0 and 1.0
- reasoning: brief explanation

Respond in JSON list format, e.g.:
[
  {"ticker": "AAPL", "action": "buy", "weight": 0.2, "confidence": 0.8, "reasoning": "Strong momentum and positive news."},
  {"ticker": "MSFT", "action": "hold", "weight": 0.1, "confidence": 0.6, "reasoning": "Neutral technicals."}
]
"""
        return prompt

    def act(
        self,
        tickers: List[str],
        price_histories: Dict[str, List[float]],
        news_data: Dict[str, List[Dict[str, Any]]],
        date: str,
        total_capital: float = None,
    ) -> List[Dict[str, Any]]:
        """
        Run joint LLM analysis for a stock pool and return per-stock trading actions.

        Args:
            tickers: List of stock tickers.
            price_histories: Dict mapping ticker to price list.
            news_data: Dict mapping ticker to news list.
            date: Analysis date.
            total_capital: Optional, total capital for allocation.
        Returns:
            List of dicts, each with ticker, action, weight, confidence, reasoning, and metadata.
        Raises:
            RuntimeError if LLM call fails or output is invalid.
        """
        prompt = self._format_portfolio_prompt(tickers, price_histories, news_data, date, total_capital)
        messages = [
            {"role": "system", "content": "You are an expert portfolio trading strategist. Analyze the following stock pool and recommend actions and allocations."},
            {"role": "user", "content": prompt},
        ]
        try:
            response = self.llm.chat(messages, temperature=0.15, max_tokens=800)
            content = response.choices[0].message.content
            result = json.loads(content)
            # Add metadata to each action
            for action in result:
                action["timestamp"] = datetime.now().isoformat()
                action["api_endpoint"] = self.base_url
                action["model_name"] = self.model_name
            return result
        except Exception as e:
            raise RuntimeError(f"PortfolioModel LLM call failed: {str(e)}") from e 
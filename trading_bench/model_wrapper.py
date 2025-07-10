import json
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

import openai


class BaseModel(ABC):
    @abstractmethod
    def should_buy(self, price_history: list[float]) -> bool:
        """Given recent price history, return True if the model signals a buy action."""
        pass

    @abstractmethod
    def act(
        self,
        ticker: str,
        price_history: list[float],
        date: str,
        quantity: int = 1,
        news_data: list[dict] = None,
    ) -> list[dict]:
        """Return list of actions in the format expected by evaluator."""
        pass


class RuleBasedModel(BaseModel):
    """A simple rule-based model that buys when the latest price is below the historical average."""

    def should_buy(self, price_history: list[float]) -> bool:
        if not price_history:
            return False
        avg_price = sum(price_history) / len(price_history)
        return price_history[-1] < avg_price

    def act(
        self,
        ticker: str,
        price_history: list[float],
        date: str,
        quantity: int = 1,
        news_data: list[dict] = None,
    ) -> list[dict]:
        """Return actions based on rule-based logic."""
        actions = []

        if self.should_buy(price_history):
            actions.append(
                {
                    'ticker': ticker,
                    'action': 'buy',
                    'timestamp': date,
                    'quantity': quantity,
                    'price': price_history[-1] if price_history else None,
                }
            )

        return actions


class AIStockAnalysisModel(BaseModel):
    """AI-powered stock analysis model that uses LLM for trend prediction with news integration."""

    def __init__(self, api_key: str = None, model_name: str = 'gpt-4'):
        """
        Initialize AI model with API credentials.

        Args:
            api_key: OpenAI API key (if None, will try to get from environment)
            model_name: LLM model to use for predictions
        """
        if api_key is None:
            import os

            api_key = os.getenv('OPENAI_API_KEY')

        self.client = openai.OpenAI(api_key=api_key)
        self.model_name = model_name

    def _format_stock_data(
        self, price_history: list[float], news_data: list[dict] = None
    ) -> str:
        """Format stock price data and news into LLM prompt."""
        if not price_history:
            return 'No price data available'

        # Calculate basic indicators
        latest_price = price_history[-1]
        if len(price_history) > 1:
            prev_price = price_history[-2]
            price_change = latest_price - prev_price
            price_change_pct = (price_change / prev_price) * 100
        else:
            price_change = 0
            price_change_pct = 0

        # Moving averages
        ma_5 = sum(price_history[-5:]) / min(5, len(price_history))
        ma_10 = sum(price_history[-10:]) / min(10, len(price_history))
        ma_20 = sum(price_history[-20:]) / min(20, len(price_history))

        # Volatility (standard deviation of last 10 prices)
        if len(price_history) >= 2:
            recent_prices = price_history[-10:]
            avg = sum(recent_prices) / len(recent_prices)
            variance = sum((p - avg) ** 2 for p in recent_prices) / len(recent_prices)
            volatility = variance**0.5
        else:
            volatility = 0

        prompt = f"""
        Stock Analysis Data:

        Current Price: ${latest_price:.2f}
        Price Change: ${price_change:.2f} ({price_change_pct:.2f}%)

        Moving Averages:
        - 5-day MA: ${ma_5:.2f}
        - 10-day MA: ${ma_10:.2f}
        - 20-day MA: ${ma_20:.2f}

        Volatility: {volatility:.2f}

        Recent Price History (last 10 days):
        {price_history[-10:]}
        """

        # Add news data if available
        if news_data and len(news_data) > 0:
            prompt += f"""

        Recent News Headlines ({len(news_data)} articles):
        """
            for i, article in enumerate(news_data, 1):
                prompt += f"""
        {i}. {article['title']} ({article.get('source', 'Unknown')})
           Date: {article.get('date', 'Unknown')}
           Snippet: {article.get('snippet', '')[:200]}...
        """
        else:
            prompt += """

        Recent News: No recent news data provided
        """

        prompt += """

        Based on this technical analysis AND news sentiment, predict the next day's trend.
        Consider how the news might impact stock price movement.
        """

        return prompt

    def _call_llm_api(self, prompt: str) -> dict[str, Any]:
        """Call LLM API for trend prediction."""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        'role': 'system',
                        'content': """You are a stock market technical analyst with expertise in both technical analysis and news sentiment analysis.

                        Analyze the provided stock data AND news headlines to predict the next day's trend.

                        Consider:
                        1. Technical indicators (price, moving averages, volatility)
                        2. News sentiment (positive, negative, neutral)
                        3. News impact on stock price (high, medium, low)

                        Respond with a JSON object containing:
                        - prediction: "BULLISH", "BEARISH", or "NEUTRAL"
                        - confidence: float between 0.0 and 1.0
                        - reasoning: brief explanation combining technical and news analysis
                        - action: "buy", "sell", or "hold"
                        - quantity: recommended quantity (1-10)
                        - news_sentiment: "positive", "negative", or "neutral"
                        - news_impact: "high", "medium", or "low"

                        Example response:
                        {
                            "prediction": "BULLISH",
                            "confidence": 0.75,
                            "reasoning": "Price above 20-day MA with positive earnings news",
                            "action": "buy",
                            "quantity": 5,
                            "news_sentiment": "positive",
                            "news_impact": "high"
                        }""",
                    },
                    {'role': 'user', 'content': prompt},
                ],
                temperature=0.1,
                max_tokens=300,
            )

            content = response.choices[0].message.content
            return json.loads(content)

        except Exception as e:
            return {
                'prediction': 'NEUTRAL',
                'confidence': 0.0,
                'reasoning': f'API Error: {str(e)}',
                'action': 'hold',
                'quantity': 0,
                'news_sentiment': 'neutral',
                'news_impact': 'low',
            }

    def should_buy(self, price_history: list[float]) -> bool:
        """
        Determine if model signals a buy action based on AI prediction.

        Args:
            price_history: List of recent stock prices

        Returns:
            bool: True if AI predicts bullish trend, False otherwise
        """
        prediction = self.get_trend_prediction(price_history)
        return prediction.get('action') == 'buy'

    def get_trend_prediction(
        self, price_history: list[float], news_data: list[dict] = None
    ) -> dict[str, Any]:
        """
        Get detailed trend prediction from AI model with news integration.

        Args:
            price_history: List of recent stock prices
            news_data: List of news articles (optional)

        Returns:
            dict: Prediction with confidence and reasoning
        """
        if not price_history:
            return {
                'prediction': 'NEUTRAL',
                'confidence': 0.0,
                'reasoning': 'No price data available',
                'action': 'hold',
                'quantity': 0,
                'news_sentiment': 'neutral',
                'news_impact': 'low',
            }

        # Format data and call LLM
        prompt = self._format_stock_data(price_history, news_data)
        result = self._call_llm_api(prompt)

        # Add metadata
        result['timestamp'] = datetime.now().isoformat()
        result['data_points'] = len(price_history)
        result['latest_price'] = price_history[-1]
        result['news_articles_count'] = len(news_data) if news_data else 0

        return result

    def act(
        self,
        ticker: str,
        price_history: list[float],
        date: str,
        quantity: int = None,
        news_data: list[dict] = None,
    ) -> list[dict]:
        """
        Get actions directly from AI model in evaluator format with news integration.

        Args:
            ticker: Stock ticker symbol
            price_history: List of recent stock prices
            date: Date for the action
            quantity: Override quantity (if None, uses AI recommendation)
            news_data: List of news articles (optional)

        Returns:
            List of actions in evaluator format
        """
        prediction = self.get_trend_prediction(price_history, news_data)
        actions = []

        action_type = prediction.get('action', 'hold')
        ai_quantity = prediction.get('quantity', 1)
        final_quantity = quantity if quantity is not None else ai_quantity

        if action_type in ['buy', 'sell'] and final_quantity > 0:
            actions.append(
                {
                    'ticker': ticker,
                    'action': action_type,
                    'timestamp': date,
                    'quantity': final_quantity,
                    'price': price_history[-1] if price_history else None,
                    'confidence': prediction.get('confidence', 0.0),
                    'reasoning': prediction.get('reasoning', 'AI recommendation'),
                    'news_sentiment': prediction.get('news_sentiment', 'neutral'),
                    'news_impact': prediction.get('news_impact', 'low'),
                    'news_articles_count': prediction.get('news_articles_count', 0),
                }
            )

        return actions

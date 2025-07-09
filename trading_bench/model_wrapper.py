from abc import ABC, abstractmethod
import json
from typing import Dict, Optional, Any
import openai
from datetime import datetime


class BaseModel(ABC):
    @abstractmethod
    def should_buy(self, price_history: list[float]) -> bool:
        """Given recent price history, return True if the model signals a buy action."""
        pass


class RuleBasedModel(BaseModel):
    """A simple rule-based model that buys when the latest price is below the historical average."""

    def should_buy(self, price_history: list[float]) -> bool:
        if not price_history:
            return False
        avg_price = sum(price_history) / len(price_history)
        return price_history[-1] < avg_price


class AIStockAnalysisModel(BaseModel):
    """AI-powered stock analysis model that uses LLM for trend prediction."""
    
    def __init__(self, api_key: str, model_name: str = "gpt-4"):
        """
        Initialize AI model with API credentials.
        
        Args:
            api_key: OpenAI API key
            model_name: LLM model to use for predictions
        """
        self.client = openai.OpenAI(api_key=api_key)
        self.model_name = model_name
        
    def _format_stock_data(self, price_history: list[float]) -> str:
        """Format stock price data into LLM prompt."""
        if not price_history:
            return "No price data available"
            
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
            volatility = variance ** 0.5
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
        
        Based on this technical analysis, predict the next day's trend.
        """
        
        return prompt
        
    def _call_llm_api(self, prompt: str) -> Dict[str, Any]:
        """Call LLM API for trend prediction."""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": """You are a stock market technical analyst. Analyze the provided stock data and predict the next day's trend.
                        
                        Respond with a JSON object containing:
                        - prediction: "BULLISH", "BEARISH", or "NEUTRAL"
                        - confidence: float between 0.0 and 1.0
                        - reasoning: brief explanation of your analysis
                        
                        Example response:
                        {
                            "prediction": "BULLISH",
                            "confidence": 0.75,
                            "reasoning": "Price is above 20-day MA with strong momentum"
                        }"""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
            
        except Exception as e:
            return {
                "prediction": "NEUTRAL",
                "confidence": 0.0,
                "reasoning": f"API Error: {str(e)}"
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
        return prediction.get("prediction") == "BULLISH"
    
    def get_trend_prediction(self, price_history: list[float]) -> Dict[str, Any]:
        """
        Get detailed trend prediction from AI model.
        
        Args:
            price_history: List of recent stock prices
            
        Returns:
            dict: Prediction with confidence and reasoning
        """
        if not price_history:
            return {
                "prediction": "NEUTRAL",
                "confidence": 0.0,
                "reasoning": "No price data available"
            }
            
        # Format data and call LLM
        prompt = self._format_stock_data(price_history)
        result = self._call_llm_api(prompt)
        
        # Add metadata
        result["timestamp"] = datetime.now().isoformat()
        result["data_points"] = len(price_history)
        result["latest_price"] = price_history[-1]
        
        return result

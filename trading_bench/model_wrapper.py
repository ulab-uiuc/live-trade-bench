from abc import ABC, abstractmethod
from typing import List

class BaseModel(ABC):
    @abstractmethod
    def should_buy(self, price_history: List[float]) -> bool:
        """Given recent price history, return True if the model signals a buy action."""
        pass

class RuleBasedModel(BaseModel):
    """A simple rule-based model that buys when the latest price is below the historical average."""
    def should_buy(self, price_history: List[float]) -> bool:
        if not price_history:
            return False
        avg_price = sum(price_history) / len(price_history)
        return price_history[-1] < avg_price

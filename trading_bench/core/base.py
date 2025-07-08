"""
Base model and configuration abstractions for trading models
"""

from abc import ABC, abstractmethod
from typing import Any


class ModelConfig(ABC):
    """Abstract base class for model configuration"""

    @abstractmethod
    def validate(self) -> bool:
        pass

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        pass


class BaseModel(ABC):
    """Abstract base class for all trading models"""

    def __init__(self, config: ModelConfig):
        self.config = config
        self.is_trained = False

    @abstractmethod
    def should_buy(self, price_history: list[float]) -> bool:
        pass

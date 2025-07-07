"""
Base model classes for trading strategies
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class ModelConfig(ABC):
    """
    Abstract base class for model configurations.
    
    This class defines the interface for model configuration objects.
    """
    
    @abstractmethod
    def validate(self) -> bool:
        """
        Validate the configuration.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def to_dict(self) -> dict:
        """
        Convert configuration to dictionary.
        
        Returns:
            Dictionary representation of the configuration
        """
        pass


class BaseModel(ABC):
    """
    Abstract base class for all trading models.
    
    This class defines the interface that all trading models must implement.
    Models can be rule-based, machine learning-based, or any other type.
    """
    
    def __init__(self, config: ModelConfig = None):
        """
        Initialize the model with optional configuration.
        
        Args:
            config: Model configuration object
        """
        self.config = config
        self.is_trained = False
    
    @abstractmethod
    def should_buy(self, price_history: List[float]) -> bool:
        """
        Determine if a buy signal should be generated based on price history.
        
        Args:
            price_history: List of historical prices (most recent last)
            
        Returns:
            True if the model signals a buy, False otherwise
        """
        pass
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the model.
        
        Returns:
            Dictionary containing model information
        """
        return {
            "model_type": self.__class__.__name__,
            "description": self.__doc__ or "No description available",
            "is_trained": self.is_trained,
            "config": self.config.to_dict() if self.config else None
        }
    
    def train(self, training_data: List) -> Dict[str, Any]:
        """
        Train the model with training data.
        
        Args:
            training_data: Training data in model-specific format
            
        Returns:
            Training metrics and results
        """
        raise NotImplementedError("Training not implemented for this model type")
    
    def save_model(self, filepath: str) -> None:
        """
        Save the model to disk.
        
        Args:
            filepath: Path where to save the model
        """
        raise NotImplementedError("Model saving not implemented for this model type")
    
    @classmethod
    def load_model(cls, filepath: str) -> 'BaseModel':
        """
        Load a model from disk.
        
        Args:
            filepath: Path to the saved model
            
        Returns:
            Loaded model instance
        """
        raise NotImplementedError("Model loading not implemented for this model type")


class RuleBasedModel(BaseModel):
    """
    A simple rule-based model that buys when the latest price is below the historical average.
    
    This is a baseline model for comparison with more sophisticated approaches.
    """
    
    def __init__(self, config: ModelConfig = None):
        super().__init__(config)
        self.is_trained = True  # Rule-based models don't need training
    
    def should_buy(self, price_history: List[float]) -> bool:
        """
        Simple rule: buy when current price is below historical average.
        
        Args:
            price_history: List of historical prices
            
        Returns:
            True if current price < average price, False otherwise
        """
        if not price_history:
            return False
        avg_price = sum(price_history) / len(price_history)
        return price_history[-1] < avg_price

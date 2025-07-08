"""
Model factory for creating different types of trading models
"""

from typing import Any

from trading_bench.core.base import BaseModel, ModelConfig
from trading_bench.models.ml import (
    BaseMLModel,
    LogisticRegressionModel,
    MLModelConfig,
    RandomForestModel,
    SVMModel,
)
from trading_bench.models.rule_based import RuleBasedConfig, RuleBasedModel


class ModelFactory:
    """
    Factory class for creating trading models.

    This class provides a centralized way to create different types of models
    with their appropriate configurations.
    """

    _model_registry: dict[str, type[BaseModel]] = {
        'rule_based': RuleBasedModel,
        'random_forest': RandomForestModel,
        'logistic_regression': LogisticRegressionModel,
        'svm': SVMModel,
    }

    _config_registry: dict[str, type[ModelConfig]] = {
        'rule_based': RuleBasedConfig,
        'random_forest': MLModelConfig,
        'logistic_regression': MLModelConfig,
        'svm': MLModelConfig,
    }

    @classmethod
    def register_model(
        cls, name: str, model_class: type[BaseModel], config_class: type[ModelConfig]
    ) -> None:
        """
        Register a new model type with the factory.

        Args:
            name: Name of the model type
            model_class: Model class
            config_class: Configuration class for the model
        """
        cls._model_registry[name] = model_class
        cls._config_registry[name] = config_class

    @classmethod
    def create_model(cls, model_type: str, **config_params) -> BaseModel:
        """
        Create a model instance with the specified configuration.

        Args:
            model_type: Type of model to create
            **config_params: Configuration parameters

        Returns:
            Model instance
        """
        if model_type not in cls._model_registry:
            raise ValueError(f'Unknown model type: {model_type}')

        model_class = cls._model_registry[model_type]
        config_class = cls._config_registry[model_type]

        # Create configuration
        config = config_class(**config_params)

        # Validate configuration
        if not config.validate():
            raise ValueError(f'Invalid configuration for {model_type}')

        # Create and return model
        return model_class(config)

    @classmethod
    def get_available_models(cls) -> list[str]:
        """Get list of available model types."""
        return list(cls._model_registry.keys())

    @classmethod
    def get_model_info(cls, model_type: str) -> dict[str, Any]:
        """
        Get information about a model type.

        Args:
            model_type: Type of model

        Returns:
            Dictionary with model information
        """
        if model_type not in cls._model_registry:
            raise ValueError(f'Unknown model type: {model_type}')

        model_class = cls._model_registry[model_type]
        config_class = cls._config_registry[model_type]

        return {
            'model_class': model_class.__name__,
            'config_class': config_class.__name__,
            'description': model_class.__doc__ or 'No description available',
            'config_schema': config_class.__annotations__
            if hasattr(config_class, '__annotations__')
            else {},
        }


# Convenience functions
def create_rule_based_model(
    rule_type: str = 'average', threshold: float = 0.0
) -> RuleBasedModel:
    """Create a rule-based model with specified configuration."""
    config = RuleBasedConfig(rule_type=rule_type, threshold=threshold)
    return RuleBasedModel(config)


def create_ml_model(model_type: str, **config_params) -> BaseMLModel:
    """Create a machine learning model with specified configuration."""
    config = MLModelConfig(model_type=model_type, **config_params)

    model_map = {
        'random_forest': RandomForestModel,
        'logistic_regression': LogisticRegressionModel,
        'svm': SVMModel,
    }

    if model_type not in model_map:
        raise ValueError(f'Unknown ML model type: {model_type}')

    return model_map[model_type](config)

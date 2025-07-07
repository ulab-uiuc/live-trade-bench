"""
Live Trading Bench - A comprehensive live backtesting framework for trading strategies
"""

from .core.bench import MLSimBench, SimBench
from .core.metrics import MetricsLogger
from .core.signal import Signal, TradeRecord
from .data.data_fetcher import fetch_price_data
from .evaluation.evaluator import MLBacktestRunner
from .models.base import BaseModel
from .models.ml_models import (
    BaseMLModel,
    LogisticRegressionModel,
    MLModelConfig,
    MLModelWrapper,
    RandomForestModel,
    SVMModel,
    create_ml_model,
)
from .models.rule_based import RuleBasedModel
from .training.trainer import CrossValidationTrainer, ModelTrainer

__all__ = [
    # Core components
    'SimBench',
    'MLSimBench',
    'MetricsLogger',
    'Signal',
    'TradeRecord',
    # Models
    'BaseModel',
    'RuleBasedModel',
    'BaseMLModel',
    'MLModelConfig',
    'RandomForestModel',
    'LogisticRegressionModel',
    'SVMModel',
    'create_ml_model',
    'MLModelWrapper',
    # Data
    'fetch_price_data',
    # Training
    'ModelTrainer',
    'CrossValidationTrainer',
    # Evaluation
    'MLBacktestRunner',
]

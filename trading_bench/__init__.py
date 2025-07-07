"""
Live Trading Bench - A comprehensive live backtesting framework for trading strategies
"""

from .core.bench import SimBench, MLSimBench
from .core.metrics import MetricsLogger
from .core.signal import Signal, TradeRecord
from .models.base import BaseModel
from .models.rule_based import RuleBasedModel
from .models.ml_models import (
    BaseMLModel,
    MLModelConfig,
    RandomForestModel,
    LogisticRegressionModel,
    SVMModel,
    create_ml_model,
    MLModelWrapper,
)
from .data.data_fetcher import fetch_price_data
from .training.trainer import ModelTrainer, CrossValidationTrainer
from .evaluation.evaluator import MLBacktestRunner

__all__ = [
    # Core components
    "SimBench",
    "MLSimBench",
    "MetricsLogger", 
    "Signal",
    "TradeRecord",
    
    # Models
    "BaseModel",
    "RuleBasedModel",
    "BaseMLModel",
    "MLModelConfig",
    "RandomForestModel",
    "LogisticRegressionModel", 
    "SVMModel",
    "create_ml_model",
    "MLModelWrapper",
    
    # Data
    "fetch_price_data",
    
    # Training
    "ModelTrainer",
    "CrossValidationTrainer",
    
    # Evaluation
    "MLBacktestRunner",
]

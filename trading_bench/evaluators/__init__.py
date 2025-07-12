"""
Trading Evaluators Package

This package provides evaluation capabilities for different types of trading strategies:
- Stock trading evaluation using StockAction classes
- Polymarket prediction market evaluation using PolymarketAction classes
- Base evaluator with common functionality and PositionTracker

All evaluators inherit from BaseEvaluator and use typed Action classes for standardized interfaces.
"""

from .action import PolymarketAction, StockAction, parse_actions

# Base classes and utilities
from .base_evaluator import BaseEvaluator, PositionTracker

# Polymarket evaluation
from .polymarket_evaluator import (
    PolymarketEvaluator,
    analyze_market_efficiency,
    calculate_kelly_criterion,
    eval_polymarket,
)

# Stock evaluation
from .stock_evaluator import StockEvaluator
from .stock_evaluator import eval_stock

__all__ = [
    # Base classes
    "BaseEvaluator",
    "PositionTracker",
    # Action classes
    "StockAction",
    "PolymarketAction",
    "parse_actions",
    # Stock evaluation
    "StockEvaluator",
    "eval_stock",
    # Polymarket evaluation
    "PolymarketEvaluator",
    "eval_polymarket",
    # Utility functions
    "calculate_kelly_criterion",
    "analyze_market_efficiency",
]

# Version info
__version__ = "2.0.0"

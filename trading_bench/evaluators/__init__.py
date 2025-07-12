"""
Trading Evaluators Package

This package provides evaluation capabilities for different types of trading strategies:
- Stock trading evaluation using StockAction classes
- Polymarket prediction market evaluation using PolymarketAction classes
- Base evaluator with common functionality and PositionTracker

All evaluators inherit from BaseEvaluator and use typed Action classes for standardized interfaces.
"""

# Base classes and utilities
from .base import BaseEvaluator, PositionTracker
from .utils import StockAction, PolymarketAction, parse_actions

# Stock evaluation
from .stock_evaluator import StockEvaluator, ReturnEvaluator, eval as eval_stock

# Polymarket evaluation  
from .polymarket_evaluator import (
    PolymarketEvaluator, 
    eval_polymarket,
    calculate_kelly_criterion,
    analyze_market_efficiency
)

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
    "ReturnEvaluator",
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
<<<<<<< HEAD
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
||||||| 8187782
=======
"""
Trading Bench Evaluators Package
"""

from .action import PolymarketAction, StockAction
from .base_account import BaseAccount
from .polymarket_account import (
    PolymarketAccount,
    PolymarketPosition,
    PolymarketTransaction,
    create_polymarket_account,
    eval_polymarket_account,
)
from .stock_account import (
    StockAccount,
    StockPosition,
    StockTransaction,
    create_stock_account,
    eval_account,
)

__all__ = [
    # Base classes
    "BaseAccount",
    # Stock trading
    "StockAccount",
    "StockPosition",
    "StockTransaction",
    "StockAction",
    "create_stock_account",
    "eval_account",
    # Polymarket trading
    "PolymarketAccount",
    "PolymarketPosition",
    "PolymarketTransaction",
    "PolymarketAction",
    "create_polymarket_account",
    "eval_polymarket_account",
]
<<<<<<< HEAD

# Version info
__version__ = "2.0.0"
>>>>>>> ce16017c508d783b9df241f101ad2be05478002e
||||||| 92f2217

# Version info
__version__ = "2.0.0"
=======
>>>>>>> c8b79d9205d163063c5816242092a9fca77de251

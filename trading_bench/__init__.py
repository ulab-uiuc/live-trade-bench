"""
Live Trading Bench - A comprehensive live backtesting framework for trading strategies
"""

from trading_bench.core.bench import SimBench
from trading_bench.core.metrics import MetricsLogger
from trading_bench.core.signal import Signal, TradeRecord
from trading_bench.data.data_fetcher import fetch_price_data
from trading_bench.evaluation.evaluator import MLBacktestRunner
from trading_bench.models.ml import MLSimBench
from trading_bench.models.rule_based import RuleBasedModel

__all__ = [
    'SimBench',
    'MLSimBench',
    'MetricsLogger',
    'Signal',
    'TradeRecord',
    'RuleBasedModel',
    'fetch_price_data',
    'MLBacktestRunner',
]

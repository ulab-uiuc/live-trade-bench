"""
Backtest System - Simple wrapper for backtesting

Pure function approach - no classes unless absolutely necessary.
"""

from typing import Any, Dict, List, Tuple

from .backtest_runner import BacktestRunner


def run_backtest(
    models: List[Tuple[str, str]],  # [(name, model_id), ...]
    initial_cash: float,
    start_date: str,
    end_date: str,
    market_type: str = "stock",
) -> Dict[str, Any]:
    """
    Run backtest with multiple models - simplified interface.

    Args:
        models: List of (name, model_id) tuples, e.g. [("GPT-4o", "gpt-4o")]
        initial_cash: Initial cash for each model
        start_date: YYYY-MM-DD
        end_date: YYYY-MM-DD
        market_type: "stock" or "polymarket"

    Returns:
        Backtest results with all models processed concurrently
    """
    runner = BacktestRunner(start_date, end_date, market_type=market_type)

    # Add models using simplified interface
    for name, model_id in models:
        runner.add_agent(
            name=name,
            initial_cash=initial_cash,
            model_name=model_id,
        )

    return runner.run()

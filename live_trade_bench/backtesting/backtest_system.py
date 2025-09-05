"""
Backtest System - Simple wrapper for backtesting

Pure function approach - no classes unless absolutely necessary.
"""

from typing import Any, Dict

from .backtest_runner import BacktestRunner


def run_backtest(
    start_date: str, end_date: str, agents_config: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Run a backtest - dead simple interface.

    Args:
        start_date: YYYY-MM-DD
        end_date: YYYY-MM-DD
        agents_config: {"agent_name": {"initial_cash": 1000, "model": "gpt-4o-mini"}}

    Returns:
        Backtest results
    """
    runner = BacktestRunner(start_date, end_date)

    # Add agents
    for name, config in agents_config.items():
        runner.add_agent(
            name=name,
            initial_cash=config.get("initial_cash", 1000.0),
            model_name=config.get("model", "gpt-4o-mini"),
        )

    return runner.run()

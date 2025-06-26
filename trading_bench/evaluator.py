from collections import deque
from datetime import datetime
from typing import Deque, Tuple
from .signal import Signal

class ReturnEvaluator:
    """
    Evaluates return percentage for a given Signal based on recent price history.
    """
    def evaluate(self, signal: Signal, history: Deque[Tuple[datetime, float]]) -> float:
        """
        Find the first price in history at or after signal.eval_time and compute return.
        If no such timestamp, use the latest price in history.

        Returns:
            return_pct: (exit_price - entry_price) / entry_price
        """
        exit_price = None
        for ts, price in history:
            if ts >= signal.eval_time:
                exit_price = price
                break
        if exit_price is None:
            # fallback to last price available
            exit_price = history[-1][1]

        return (exit_price - signal.entry_price) / signal.entry_price

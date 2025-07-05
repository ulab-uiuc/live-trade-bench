from collections import deque
from datetime import datetime
from typing import List

from .signal import Signal, TradeRecord


class ReturnEvaluator:
    """
    Evaluates return percentage for a given Signal based on recent price history.
    """

    def evaluate(self, signal: Signal, history: deque[tuple[datetime, float]]) -> TradeRecord:
        """
        Find the first price in history at or after signal.eval_time and compute return.
        If no such timestamp, use the latest price in history.

        Returns:
            TradeRecord: Complete trade record with all metrics
        """
        exit_price = None
        exit_time = None
        high_during_trade = signal.entry_price
        low_during_trade = signal.entry_price
        
        # Calculate price range during trade period
        for ts, price in history:
            if ts >= signal.entry_time and ts <= signal.eval_time:
                high_during_trade = max(high_during_trade, price)
                low_during_trade = min(low_during_trade, price)
            
            if ts >= signal.eval_time:
                exit_price = price
                exit_time = ts
                break
                
        if exit_price is None:
            # fallback to last price available
            exit_price = history[-1][1]
            exit_time = history[-1][0]

        return_pct = (exit_price - signal.entry_price) / signal.entry_price
        trade_duration = (exit_time - signal.entry_time).days
        
        return TradeRecord(
            entry_time=signal.entry_time,
            entry_price=signal.entry_price,
            exit_time=exit_time,
            exit_price=exit_price,
            return_pct=return_pct,
            trade_duration=trade_duration,
            high_during_trade=high_during_trade,
            low_during_trade=low_during_trade
        )

from collections import deque
from datetime import datetime
from pathlib import Path

from trading_bench.core.signal import Signal, TradeRecord


class ReturnEvaluator:
    """
    Evaluates return percentage for a given Signal based on recent price history.
    """

    def evaluate(
        self, signal: Signal, history: deque[tuple[datetime, float]]
    ) -> TradeRecord:
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

        # Ensure exit_time is not None
        assert exit_time is not None, 'Exit time should not be None'

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
            low_during_trade=low_during_trade,
        )


class MLBacktestRunner:
    # TODO: We may move this class to a more appropriate location, as it is essentially a process of ML model training combined with backtesting.

    """Runner for ML model backtesting (prediction only)"""

    def __init__(self, data_dir: str = './data', models_dir: str = './models'):
        self.data_dir = Path(data_dir)
        self.models_dir = Path(models_dir)

    def load_and_backtest(
        self,
        ticker: str,
        test_start: str,
        test_end: str,
        model_path: str,
        eval_delay: int = 5,
        resolution: str = 'D',
    ) -> dict:
        """
        Load a pre-trained model and run backtest

        Args:
            ticker: Stock ticker symbol
            test_start: Test start date
            test_end: Test end date
            model_path: Path to saved model
            eval_delay: Evaluation delay
            resolution: Data resolution

        Returns:
            Backtest results
        """
        print(f'Loading model from {model_path}...')

        from trading_bench.models.ml import MLSimBench

        backtest_result = MLSimBench.from_trained_model(
            ticker=ticker,
            start_date=test_start,
            end_date=test_end,
            data_dir=str(self.data_dir),
            model_path=model_path,
            eval_delay=eval_delay,
            resolution=resolution,
        ).run_with_model_info()

        return backtest_result

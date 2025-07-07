from collections import deque
from datetime import datetime
from pathlib import Path

from ..core.signal import Signal, TradeRecord
from ..models.ml_models import MLModelConfig
from ..training.trainer import ModelTrainer


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
    """Runner for ML model backtesting with multiple models"""

    def __init__(self, data_dir: str = './data', models_dir: str = './models'):
        self.data_dir = Path(data_dir)
        self.models_dir = Path(models_dir)
        self.trainer = ModelTrainer(str(self.data_dir))

    def train_and_backtest(
        self,
        ticker: str,
        train_start: str,
        train_end: str,
        test_start: str,
        test_end: str,
        model_config: MLModelConfig = None,
        eval_delay: int = 5,
        resolution: str = 'D',
    ) -> dict:
        """
        Train a model and then backtest it

        Args:
            ticker: Stock ticker symbol
            train_start: Training start date
            train_end: Training end date
            test_start: Testing start date
            test_end: Testing end date
            model_config: Model configuration
            eval_delay: Evaluation delay
            resolution: Data resolution

        Returns:
            Complete training and backtest results
        """
        if model_config is None:
            model_config = MLModelConfig(model_type='random_forest')

        # Prepare training data
        print(f'Preparing training data for {ticker}...')
        training_data = self.trainer.prepare_training_data(
            ticker, train_start, train_end, resolution
        )

        # Train model
        print(f'Training {model_config.model_type} model...')
        model_save_path = (
            self.models_dir / f'{ticker}_{model_config.model_type}_model.pkl'
        )
        self.models_dir.mkdir(parents=True, exist_ok=True)

        training_result = self.trainer.train_model(
            training_data=training_data,
            config=model_config,
            model_save_path=str(model_save_path),
        )

        # Backtest the trained model
        print(f'Running backtest for {ticker}...')
        from ..core.bench import MLSimBench

        backtest_result = MLSimBench.from_trained_model(
            ticker=ticker,
            start_date=test_start,
            end_date=test_end,
            data_dir=str(self.data_dir),
            model_path=str(model_save_path),
            eval_delay=eval_delay,
            resolution=resolution,
        ).run_with_model_info()

        return {
            'training': training_result,
            'backtest': backtest_result,
            'model_path': str(model_save_path),
        }

    def compare_models(
        self,
        ticker: str,
        train_start: str,
        train_end: str,
        test_start: str,
        test_end: str,
        eval_delay: int = 5,
        resolution: str = 'D',
    ) -> dict:
        """
        Train multiple models and compare their backtest performance

        Args:
            ticker: Stock ticker symbol
            train_start: Training start date
            train_end: Training end date
            test_start: Testing start date
            test_end: Testing end date
            eval_delay: Evaluation delay
            resolution: Data resolution

        Returns:
            Comparison results for all models
        """
        # Define model configurations
        model_configs = {
            'random_forest': MLModelConfig(
                model_type='random_forest',
                n_estimators=100,
                max_depth=10,
                random_state=42,
            ),
            'logistic_regression': MLModelConfig(
                model_type='logistic_regression', random_state=42
            ),
            'svm': MLModelConfig(
                model_type='svm', kernel='rbf', C=1.0, random_state=42
            ),
        }

        results = {}

        for model_name, config in model_configs.items():
            print(f'\n=== Training and testing {model_name} ===')

            try:
                result = self.train_and_backtest(
                    ticker=ticker,
                    train_start=train_start,
                    train_end=train_end,
                    test_start=test_start,
                    test_end=test_end,
                    model_config=config,
                    eval_delay=eval_delay,
                    resolution=resolution,
                )

                results[model_name] = result

                # Print summary
                training_acc = result['training']['metrics']['accuracy']
                backtest_return = result['backtest']['backtest_results']['total_return']
                print(f'{model_name}:')
                print(f'  Training Accuracy: {training_acc:.4f}')
                print(f'  Backtest Return: {backtest_return:.4f}')

            except Exception as e:
                print(f'Error with {model_name}: {e}')
                results[model_name] = {'error': str(e)}

        return results

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

        from ..core.bench import MLSimBench

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

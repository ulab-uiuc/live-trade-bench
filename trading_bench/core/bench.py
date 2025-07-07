import json
from collections import defaultdict, deque
from datetime import datetime
from pathlib import Path

from ..data.data_fetcher import fetch_price_data
from ..evaluation.evaluator import ReturnEvaluator
from ..models.base import BaseModel
from ..models.ml_models import BaseMLModel, MLModelWrapper
from ..visualization.visualizer import BacktestVisualizer
from .metrics import MetricsLogger
from .signal import Signal


class SimBench:
    """
    Simulated backtest bench that asks a model for buy signals and evaluates returns.
    Uses the updated yfinance-based fetch_price_data to retrieve OHLCV data.
    """

    def __init__(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
        data_dir: str,
        model: BaseModel,
        eval_delay: int = 5,
        resolution: str = 'D',
    ):
        self.ticker = ticker
        self.start_date = start_date
        self.end_date = end_date
        self.data_dir = data_dir
        self.model = model
        self.eval_delay = eval_delay
        self.resolution = resolution

        # Fetch and save price data (yfinance) into yfinance_data/price_data
        fetch_price_data(
            ticker=self.ticker,
            start_date=self.start_date,
            end_date=self.end_date,
            data_dir=self.data_dir,
            resolution=self.resolution,
        )

        # Load fetched JSON data from yfinance_data
        data_path = (
            Path(self.data_dir)
            / 'yfinance_data'
            / 'price_data'
            / f'{self.ticker}_data_formatted.json'
        )
        if not data_path.is_file():
            raise FileNotFoundError(f'Expected data file not found at {data_path}')

        with open(data_path, encoding='utf-8') as f:
            raw_data = json.load(f)

        # Parse into list of (datetime, close_price)
        parsed: list[tuple[datetime, float]] = []
        for date_str, v in raw_data.items():
            date = datetime.fromisoformat(date_str)
            # v is a dict with keys open, high, low, close, volume
            price = float(v.get('close', v))
            parsed.append((date, price))

        # Sort chronologically and initialize history deque
        self.data: list[tuple[datetime, float]] = sorted(parsed, key=lambda x: x[0])
        self.history: deque[tuple[datetime, float]] = deque(self.data)

        self.evaluator = ReturnEvaluator()
        self.logger = MetricsLogger()
        self.visualizer = BacktestVisualizer(self.logger)

    def run(self) -> dict[str, float]:
        prices = [price for _, price in self.data]
        n = len(prices)

        # 1. start with an empty "past history" and a place to stash pending signals
        self.history = deque()
        pending: dict[int, list[Signal]] = defaultdict(list)

        for idx, (date, price) in enumerate(self.data):
            # 2. append this step into your history
            self.history.append((date, price))

            # 3. if model says BUY, schedule evaluation at idx + eval_delay
            if self.model.should_buy([p for _, p in self.history]):
                eval_idx = min(idx + self.eval_delay, n - 1)
                eval_time = self.data[eval_idx][0]
                signal = Signal(date, price, eval_time)
                pending[eval_idx].append(signal)

            # 4. now check if any scheduled signals are due at this idx
            if idx in pending:
                for signal in pending.pop(idx):
                    # you might want to pass only the slice of history from buy→eval
                    # but ReturnEvaluator could also just use signal.price + actual price at eval_time
                    history_slice = deque(list(self.history)[-self.eval_delay - 1 :])
                    trade_record = self.evaluator.evaluate(signal, history_slice)
                    self.logger.record(trade_record)

        return self.logger.summary()

    def generate_charts(self, save: bool = True) -> dict[str, str | None]:
        """
        Generate all backtesting charts.

        Args:
            save: Whether to save charts to files

        Returns:
            Dictionary of chart file paths
        """
        return self.visualizer.generate_all_charts(self.ticker, save)


class MLSimBench(SimBench):
    """
    Extended SimBench that supports machine learning models
    """

    def __init__(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
        data_dir: str,
        model: BaseModel,
        eval_delay: int = 5,
        resolution: str = 'D',
        model_info: dict = None,
    ):
        super().__init__(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            data_dir=data_dir,
            model=model,
            eval_delay=eval_delay,
            resolution=resolution,
        )
        self.model_info = model_info or {}

    @classmethod
    def from_trained_model(
        cls,
        ticker: str,
        start_date: str,
        end_date: str,
        data_dir: str,
        model_path: str,
        eval_delay: int = 5,
        resolution: str = 'D',
    ) -> 'MLSimBench':
        """
        Create MLSimBench from a saved trained model

        Args:
            ticker: Stock ticker symbol
            start_date: Start date for backtesting
            end_date: End date for backtesting
            model_path: Path to saved model file
            eval_delay: Evaluation delay
            resolution: Data resolution

        Returns:
            MLSimBench instance
        """
        # Load the trained model
        if model_path.endswith('.pkl'):
            # Load from pickle file
            ml_model = BaseMLModel.load_model(model_path)
        else:
            raise ValueError('Model path must be a .pkl file')

        # Wrap the ML model
        wrapped_model = MLModelWrapper(ml_model)

        # Create model info
        model_info = {
            'model_path': model_path,
            'model_type': ml_model.config.model_type,
            'is_trained': ml_model.is_trained,
        }

        return cls(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            data_dir=data_dir,
            model=wrapped_model,
            eval_delay=eval_delay,
            resolution=resolution,
            model_info=model_info,
        )

    def run_with_model_info(self) -> dict:
        """
        Run backtest and include model information in results

        Returns:
            Dictionary with backtest results and model info
        """
        backtest_results = self.run()

        return {
            'backtest_results': backtest_results,
            'model_info': self.model_info,
            'ticker': self.ticker,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'eval_delay': self.eval_delay,
        }

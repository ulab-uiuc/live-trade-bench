import os
import json
from collections import deque
from datetime import datetime
from typing import List, Tuple, Dict, Optional

from .model_wrapper import BaseModel
from .signal import Signal
from .evaluator import ReturnEvaluator
from .metrics import MetricsLogger
from .data_fetcher import fetch_price_data
from collections import defaultdict

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
        resolution: str = 'D'
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
            resolution=self.resolution
        )

        # Load fetched JSON data from yfinance_data
        data_path = os.path.join(
            self.data_dir,
            'yfinance_data',
            'price_data',
            f"{self.ticker}_data_formatted.json"
        )
        if not os.path.isfile(data_path):
            raise FileNotFoundError(f"Expected data file not found at {data_path}")

        with open(data_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)

        # Parse into list of (datetime, close_price)
        parsed: List[Tuple[datetime, float]] = []
        for date_str, v in raw_data.items():
            date = datetime.fromisoformat(date_str)
            # v is a dict with keys open, high, low, close, volume
            price = float(v.get('close', v))
            parsed.append((date, price))

        # Sort chronologically and initialize history deque
        self.data: List[Tuple[datetime, float]] = sorted(parsed, key=lambda x: x[0])
        self.history: deque = deque(self.data)

        self.evaluator = ReturnEvaluator()
        self.logger = MetricsLogger()

    def run(self) -> Dict[str, float]:
        prices = [price for _, price in self.data]
        n = len(prices)

        # 1. start with an empty "past history" and a place to stash pending signals
        self.history = deque()  
        pending: Dict[int, List[Signal]] = defaultdict(list)

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
                    ret = self.evaluator.evaluate(signal, list(self.history)[-self.eval_delay-1:])
                    self.logger.record(ret)

        return self.logger.summary()
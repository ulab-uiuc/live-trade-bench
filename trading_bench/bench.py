import json
from collections import defaultdict, deque
from datetime import datetime
from pathlib import Path

from trading_bench.data_fetcher import fetch_price_data
from trading_bench.evaluator import ReturnEvaluator
from trading_bench.metrics import MetricsLogger
from trading_bench.model_wrapper import BaseModel
from trading_bench.signal import Signal, TradeRecord
from trading_bench.visualization import BacktestVisualizer


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

        # Fetch price data (yfinance)
        raw_data = fetch_price_data(
            ticker=self.ticker,
            start_date=self.start_date,
            end_date=self.end_date,
            resolution=self.resolution,
        )

        # Save fetched data to file for future use
        data_path = (
            Path(self.data_dir)
            / 'yfinance_data'
            / 'price_data'
            / f'{self.ticker}_data_formatted.json'
        )
        data_path.parent.mkdir(parents=True, exist_ok=True)
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump(raw_data, f, indent=2)

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

    def _eval_action_with_data(self, signal: Signal) -> TradeRecord:
        """Evaluate a signal using existing price data"""

        # Find entry and exit prices from existing data
        entry_price = signal.entry_price  # Already available in signal
        exit_price = None

        # Find exit price from existing data
        for date, price in self.data:
            if date >= signal.eval_time:
                exit_price = price
                break

        if exit_price is None:
            # Fallback to last available price
            exit_price = self.data[-1][1]

        # Calculate metrics
        return_pct = (exit_price - entry_price) / entry_price if entry_price > 0 else 0
        trade_duration = (signal.eval_time - signal.entry_time).days

        return TradeRecord(
            entry_time=signal.entry_time,
            entry_price=entry_price,
            exit_time=signal.eval_time,
            exit_price=exit_price,
            return_pct=return_pct,
            trade_duration=trade_duration,
        )

    def eval(self, actions: dict | list[dict]) -> dict | list[dict]:
        """
        Evaluate trading actions and return profit/loss results.

        Args:
            actions: Single action dict or list of action dicts
                    Each action should contain:
                    - ticker: str (stock symbol)
                    - entry_date: str (YYYY-MM-DD format)
                    - exit_date: str (YYYY-MM-DD format)
                    - quantity: int (number of shares)

        Returns:
            Single result dict or list of result dicts with profit/loss information
        """
        if isinstance(actions, dict):
            return self._eval_single_action(actions)
        elif isinstance(actions, list):
            return [self._eval_single_action(action) for action in actions]
        else:
            raise ValueError('actions must be a dict or list of dicts')

    def _eval_single_action(self, action: dict) -> dict:
        """Evaluate a single trading action"""
        ticker = action.get('ticker', self.ticker)
        entry_date = action.get('entry_date')
        exit_date = action.get('exit_date')
        quantity = action.get('quantity', 1)

        if not entry_date or not exit_date:
            raise ValueError('entry_date and exit_date are required')

        # Fetch data for this specific ticker and date range
        raw_data = fetch_price_data(
            ticker=ticker,
            start_date=entry_date,
            end_date=exit_date,
            resolution=self.resolution,
        )

        # Parse data
        parsed: list[tuple[datetime, float]] = []
        for date_str, v in raw_data.items():
            date = datetime.fromisoformat(date_str)
            price = float(v.get('close', v))
            parsed.append((date, price))

        # Sort chronologically
        data = sorted(parsed, key=lambda x: x[0])

        if not data:
            return {
                'ticker': ticker,
                'entry_date': entry_date,
                'exit_date': exit_date,
                'quantity': quantity,
                'entry_price': 0,
                'exit_price': 0,
                'profit_loss': 0,
                'return_pct': 0,
                'error': 'No data available for the specified date range',
            }

        # Find entry and exit prices
        entry_price = None
        exit_price = None

        # Find closest entry date
        entry_dt = datetime.fromisoformat(entry_date)
        for date, price in data:
            if date >= entry_dt:
                entry_price = price
                break

        # Find closest exit date
        exit_dt = datetime.fromisoformat(exit_date)
        for date, price in reversed(data):
            if date <= exit_dt:
                exit_price = price
                break

        # Fallback to first/last available prices
        if entry_price is None:
            entry_price = data[0][1]
        if exit_price is None:
            exit_price = data[-1][1]

        # Calculate profit/loss
        profit_loss = (exit_price - entry_price) * quantity
        return_pct = (exit_price - entry_price) / entry_price if entry_price > 0 else 0

        return {
            'ticker': ticker,
            'entry_date': entry_date,
            'exit_date': exit_date,
            'quantity': quantity,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'profit_loss': profit_loss,
            'return_pct': return_pct,
            'total_investment': entry_price * quantity,
            'final_value': exit_price * quantity,
        }

    def run(self) -> dict[str, float]:
        """
        Run model-based backtesting simulation.
        The model generates signals, which are then evaluated using the eval method.
        """
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
                signal = Signal(date, price, eval_time, ticker=self.ticker)
                pending[eval_idx].append(signal)

            # 4. now check if any scheduled signals are due at this idx
            if idx in pending:
                for signal in pending.pop(idx):
                    # Use existing data for evaluation instead of fetching again
                    trade_record = self._eval_action_with_data(signal)
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

"""
Configuration management for the Live Trading Bench framework
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class DataConfig:
    """Configuration for data fetching and storage"""

    data_dir: str = './data'
    cache_enabled: bool = True
    max_retries: int = 3
    request_delay: float = 1.0


@dataclass
class BacktestConfig:
    """Configuration for backtesting"""

    eval_delay: int = 5
    resolution: str = 'D'
    commission_rate: float = 0.001
    slippage: float = 0.0005


@dataclass
class ModelConfig:
    """Configuration for model training and evaluation"""

    test_size: float = 0.2
    random_state: int = 42
    cross_validation_folds: int = 5
    models_dir: str = './models'


@dataclass
class VisualizationConfig:
    """Configuration for visualization"""

    output_dir: str = './charts'
    dpi: int = 300
    figsize: tuple = (12, 8)
    style: str = 'seaborn-v0_8'


@dataclass
class TradingBenchConfig:
    """Main configuration class for the trading bench framework"""

    data: DataConfig = None
    backtest: BacktestConfig = None
    model: ModelConfig = None
    visualization: VisualizationConfig = None

    def __post_init__(self):
        """Initialize default configurations if not provided"""
        if self.data is None:
            self.data = DataConfig()
        if self.backtest is None:
            self.backtest = BacktestConfig()
        if self.model is None:
            self.model = ModelConfig()
        if self.visualization is None:
            self.visualization = VisualizationConfig()

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'data': self.data.__dict__,
            'backtest': self.backtest.__dict__,
            'model': self.model.__dict__,
            'visualization': self.visualization.__dict__,
        }

    @classmethod
    def from_dict(cls, config_dict: dict[str, Any]) -> 'TradingBenchConfig':
        """Create configuration from dictionary"""
        return cls(
            data=DataConfig(**config_dict.get('data', {})),
            backtest=BacktestConfig(**config_dict.get('backtest', {})),
            model=ModelConfig(**config_dict.get('model', {})),
            visualization=VisualizationConfig(**config_dict.get('visualization', {})),
        )

    def save(self, filepath: str) -> None:
        """Save configuration to file"""
        import json

        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, filepath: str) -> 'TradingBenchConfig':
        """Load configuration from file"""
        import json

        with open(filepath) as f:
            config_dict = json.load(f)
        return cls.from_dict(config_dict)


DEFAULT_CONFIG = TradingBenchConfig()

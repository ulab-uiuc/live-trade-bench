"""
Machine Learning Models for Live Trading Bench
Load trained models and perform predictions (should_buy).
"""

#TODO: To be refined

import pickle
from abc import abstractmethod
from typing import Any

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC

from trading_bench.core.base import BaseModel, ModelConfig
from trading_bench.core.bench import SimBench


class MLModelConfig(ModelConfig):
    """Configuration for machine learning models"""

    def __init__(
        self,
        model_type: str = 'random_forest',
        **model_params: Any,
    ):
        self.model_type = model_type
        self.model_params = model_params

    def validate(self) -> bool:
        """Validate the configuration."""
        valid_types = ['random_forest', 'logistic_regression', 'svm']
        return self.model_type in valid_types

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'model_type': self.model_type,
            'model_params': self.model_params,
        }


class BaseMLModel(BaseModel):
    """Abstract base class for machine learning models (prediction only)"""

    def __init__(self, config: MLModelConfig):
        super().__init__(config)
        self.model = None

    @abstractmethod
    def _create_model(self) -> Any:
        pass

    @abstractmethod
    def _extract_features(self, price_history: list[float]) -> np.ndarray:
        pass

    def should_buy(self, price_history: list[float]) -> bool:
        if not self.is_trained:
            raise RuntimeError('Model must be trained before making predictions')
        features = self._extract_features(price_history)
        prediction = self.model.predict([features])[0]
        return bool(prediction)

    @classmethod
    def load_model(cls, filepath: str) -> 'BaseMLModel':
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        config = model_data['config']
        model_map = {
            'random_forest': RandomForestModel,
            'logistic_regression': LogisticRegressionModel,
            'svm': SVMModel,
        }

        if config.model_type not in model_map:
            raise ValueError(f'Unknown model type: {config.model_type}')

        instance = model_map[config.model_type](config)
        instance.model = model_data['model']
        instance.is_trained = model_data['is_trained']
        return instance


class RandomForestModel(BaseMLModel):
    def _create_model(self) -> RandomForestClassifier:
        return RandomForestClassifier(**self.config.model_params)

    def _extract_features(self, price_history: list[float]) -> np.ndarray:
        """Extract technical indicators as features (set as an example)"""
        if len(price_history) < 20:
            # Pad with the first price if not enough history
            padded_history = [price_history[0]] * (
                20 - len(price_history)
            ) + price_history
        else:
            padded_history = price_history[-20:]  # Use last 20 prices

        prices = np.array(padded_history)

        # Calculate technical indicators
        features = []

        # Price-based features
        features.extend(
            [
                prices[-1],  # Current price
                np.mean(prices),  # Mean price
                np.std(prices),  # Price volatility
                prices[-1] / prices[0] - 1,  # Total return
            ]
        )

        # Moving averages
        features.extend(
            [
                np.mean(prices[-5:]),  # 5-period MA
                np.mean(prices[-10:]),  # 10-period MA
                np.mean(prices[-20:]),  # 20-period MA
            ]
        )

        # Price momentum
        features.extend(
            [
                prices[-1] / prices[-5] - 1,  # 5-period momentum
                prices[-1] / prices[-10] - 1,  # 10-period momentum
                prices[-1] / prices[-20] - 1,  # 20-period momentum
            ]
        )

        # Volatility features
        returns = np.diff(prices) / prices[:-1]
        features.extend(
            [
                np.std(returns[-5:]),  # 5-period volatility
                np.std(returns[-10:]),  # 10-period volatility
                np.std(returns[-20:]),  # 20-period volatility
            ]
        )

        # RSI-like indicator
        gains = np.where(returns > 0, returns, 0)
        losses = np.where(returns < 0, -returns, 0)
        avg_gain = np.mean(gains[-14:]) if len(gains) >= 14 else np.mean(gains)
        avg_loss = np.mean(losses[-14:]) if len(losses) >= 14 else np.mean(losses)
        rs = avg_gain / avg_loss if avg_loss != 0 else 0
        rsi = 100 - (100 / (1 + rs))
        features.append(rsi)

        return np.array(features)


class LogisticRegressionModel(BaseMLModel):
    def _create_model(self) -> LogisticRegression:
        return LogisticRegression(**self.config.model_params)

    def _extract_features(self, price_history: list[float]) -> np.ndarray:
        return np.array([price_history[-20]])


class SVMModel(BaseMLModel):
    def _create_model(self) -> SVC:
        return SVC(probability=True, **self.config.model_params)

    def _extract_features(self, price_history: list[float]) -> np.ndarray:
        return np.array([price_history[-20]])


def create_ml_model(config: MLModelConfig) -> BaseMLModel:
    model_map = {
        'random_forest': RandomForestModel,
        'logistic_regression': LogisticRegressionModel,
        'svm': SVMModel,
    }
    if config.model_type not in model_map:
        raise ValueError(f'Unknown model type: {config.model_type}')
    return model_map[config.model_type](config)


class MLModelWrapper(BaseModel):
    """Wrapper to make ML models compatible with SimBench"""

    def __init__(self, ml_model: BaseMLModel):
        super().__init__(ml_model.config)
        self.ml_model = ml_model

    def should_buy(self, price_history: list[float]) -> bool:
        return self.ml_model.should_buy(price_history)


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
        """
        if model_path.endswith('.pkl'):
            ml_model = BaseMLModel.load_model(model_path)
        else:
            raise ValueError('Model path must be a .pkl file')
        wrapped_model = MLModelWrapper(ml_model)
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

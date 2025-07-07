"""
Machine Learning Models for Live Trading Bench
Supports training and prediction for various ML algorithms
"""

import pickle
from abc import abstractmethod
from typing import Any

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from .base import BaseModel, ModelConfig


class MLModelConfig(ModelConfig):
    """Configuration for machine learning models"""

    def __init__(
        self,
        model_type: str = 'random_forest',
        test_size: float = 0.2,
        random_state: int = 42,
        **model_params: Any,
    ):
        self.model_type = model_type
        self.test_size = test_size
        self.random_state = random_state
        self.model_params = model_params

    def validate(self) -> bool:
        """Validate the configuration."""
        valid_types = ['random_forest', 'logistic_regression', 'svm']
        return (
            self.model_type in valid_types
            and 0 < self.test_size < 1
            and isinstance(self.random_state, int)
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'model_type': self.model_type,
            'test_size': self.test_size,
            'random_state': self.random_state,
            'model_params': self.model_params,
        }


class BaseMLModel(BaseModel):
    """Abstract base class for machine learning models"""

    def __init__(self, config: MLModelConfig):
        super().__init__(config)
        self.model = None
        self.scaler = StandardScaler()

    @abstractmethod
    def _create_model(self) -> Any:
        """Create the specific ML model instance"""
        pass

    @abstractmethod
    def _extract_features(self, price_history: list[float]) -> np.ndarray:
        """Extract features from price history"""
        pass

    def train(self, training_data: list[tuple[list[float], bool]]) -> dict[str, Any]:
        """
        Train the model with historical data

        Args:
            training_data: List of (price_history, should_buy) tuples

        Returns:
            Training metrics
        """
        if not training_data:
            raise ValueError('Training data cannot be empty')

        # Extract features and labels
        X = []
        y = []

        for price_history, should_buy in training_data:
            features = self._extract_features(price_history)
            X.append(features)
            y.append(1 if should_buy else 0)

        X = np.array(X)
        y = np.array(y)

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=self.config.test_size, random_state=self.config.random_state
        )

        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Create and train model
        self.model = self._create_model()
        self.model.fit(X_train_scaled, y_train)

        # Evaluate
        y_pred = self.model.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)

        self.is_trained = True

        return {
            'accuracy': accuracy,
            'train_samples': len(X_train),
            'test_samples': len(X_test),
            'classification_report': classification_report(y_test, y_pred),
        }

    def should_buy(self, price_history: list[float]) -> bool:
        """Predict whether to buy based on price history"""
        if not self.is_trained:
            raise RuntimeError('Model must be trained before making predictions')

        features = self._extract_features(price_history)
        features_scaled = self.scaler.transform([features])
        prediction = self.model.predict(features_scaled)[0]

        return bool(prediction)

    def save_model(self, filepath: str) -> None:
        """Save the trained model to disk"""
        if not self.is_trained:
            raise RuntimeError('Cannot save untrained model')

        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'config': self.config,
            'is_trained': self.is_trained,
        }

        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)

    @classmethod
    def load_model(cls, filepath: str) -> 'BaseMLModel':
        """Load a trained model from disk"""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)

        # Create the correct model instance based on config
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
        instance.scaler = model_data['scaler']
        instance.is_trained = model_data['is_trained']

        return instance


class RandomForestModel(BaseMLModel):
    """Random Forest classifier for trading signals"""

    def _create_model(self) -> RandomForestClassifier:
        return RandomForestClassifier(
            random_state=self.config.random_state, **self.config.model_params
        )

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
    """Logistic Regression model for trading signals"""

    def _create_model(self) -> LogisticRegression:
        return LogisticRegression(
            random_state=self.config.random_state, **self.config.model_params
        )

    def _extract_features(self, price_history: list[float]) -> np.ndarray:
        """Extract features for logistic regression (set as an example)"""
        if len(price_history) < 20:
            padded_history = [price_history[0]] * (
                20 - len(price_history)
            ) + price_history
        else:
            padded_history = price_history[-20:]

        prices = np.array(padded_history)

        features = [
            prices[-1],  # Current price
            np.mean(prices),  # Mean price
            prices[-1] / prices[0] - 1,  # Total return
            np.mean(prices[-5:]),  # 5-period MA
            np.std(prices),  # Volatility
        ]

        return np.array(features)


class SVMModel(BaseMLModel):
    """Support Vector Machine model for trading signals"""

    def _create_model(self) -> SVC:
        return SVC(
            random_state=self.config.random_state,
            probability=True,
            **self.config.model_params,
        )

    def _extract_features(self, price_history: list[float]) -> np.ndarray:
        """Extract features for SVM (set as an example)"""
        if len(price_history) < 20:
            padded_history = [price_history[0]] * (
                20 - len(price_history)
            ) + price_history
        else:
            padded_history = price_history[-20:]

        prices = np.array(padded_history)

        features = [
            prices[-1],  # Current price
            np.mean(prices),  # Mean price
            np.std(prices),  # Volatility
            prices[-1] / prices[0] - 1,  # Total return
            np.mean(prices[-5:]),  # 5-period MA
            np.mean(prices[-10:]),  # 10-period MA
        ]

        return np.array(features)


def create_ml_model(config: MLModelConfig) -> BaseMLModel:
    """Factory function to create ML models"""
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
        """Delegate to the ML model's should_buy method"""
        return self.ml_model.should_buy(price_history)

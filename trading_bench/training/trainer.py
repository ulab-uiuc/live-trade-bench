"""
Training module for machine learning models
Generates training data and trains ML models for trading signals
"""

import json
from datetime import datetime
from pathlib import Path

import numpy as np

from ..data.data_fetcher import fetch_price_data
from ..models.ml_models import MLModelConfig, create_ml_model
from ..utils import setup_logging


class TrainingDataGenerator:
    """Generate training data from historical price data"""

    def __init__(self, lookback_window: int = 20, future_window: int = 5):
        self.lookback_window = lookback_window
        self.future_window = future_window

    def generate_training_data(
        self, price_data: list[tuple[datetime, float]]
    ) -> list[tuple[list[float], bool]]:
        """
        Generate training data from historical prices

        Args:
            price_data: List of (datetime, price) tuples

        Returns:
            List of (price_history, should_buy) tuples
        """
        training_data = []
        prices = [price for _, price in price_data]

        for i in range(self.lookback_window, len(prices) - self.future_window):
            # Extract price history window
            price_history = prices[i - self.lookback_window : i]

            # Calculate future return to determine if we should have bought
            current_price = prices[i]
            future_prices = prices[i : i + self.future_window + 1]
            max_future_price = max(future_prices)

            # Define buy signal: if future price increases by more than 2%
            should_buy = (max_future_price / current_price - 1) > 0.02

            training_data.append((price_history, should_buy))

        return training_data


class ModelTrainer:
    """Train machine learning models for trading signals"""

    def __init__(self, data_dir: str = './data'):
        self.data_dir = Path(data_dir)
        self.data_generator = TrainingDataGenerator()
        setup_logging()

    def prepare_training_data(
        self, ticker: str, start_date: str, end_date: str, resolution: str = 'D'
    ) -> list[tuple[list[float], bool]]:
        """
        Prepare training data for a specific ticker and time period

        Args:
            ticker: Stock ticker symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            resolution: Data resolution

        Returns:
            Training data
        """
        # Fetch price data
        fetch_price_data(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            data_dir=str(self.data_dir),
            resolution=resolution,
        )

        # Load price data
        data_path = (
            self.data_dir
            / 'yfinance_data'
            / 'price_data'
            / f'{ticker}_data_formatted.json'
        )

        if not data_path.is_file():
            raise FileNotFoundError(f'Data file not found: {data_path}')

        with open(data_path, encoding='utf-8') as f:
            raw_data = json.load(f)

        # Parse into list of (datetime, price)
        price_data = []
        for date_str, v in raw_data.items():
            date = datetime.fromisoformat(date_str)
            price = float(v.get('close', v))
            price_data.append((date, price))

        # Sort chronologically
        price_data.sort(key=lambda x: x[0])

        # Generate training data
        return self.data_generator.generate_training_data(price_data)

    def train_model(
        self,
        training_data: list[tuple[list[float], bool]],
        config: MLModelConfig,
        model_save_path: str = None,
    ) -> dict:
        """
        Train a machine learning model

        Args:
            training_data: Training data
            config: Model configuration
            model_save_path: Path to save the trained model

        Returns:
            Training results
        """
        # Create and train model
        model = create_ml_model(config)
        training_metrics = model.train(training_data)

        # Save model if path provided
        if model_save_path:
            model.save_model(model_save_path)

        return {'model': model, 'metrics': training_metrics, 'config': config}

    def train_multiple_models(
        self,
        training_data: list[tuple[list[float], bool]],
        models_dir: str = './models',
    ) -> dict:
        """
        Train multiple models and compare performance

        Args:
            training_data: Training data
            models_dir: Directory to save trained models

        Returns:
            Training results for all models
        """
        models_dir = Path(models_dir)
        models_dir.mkdir(parents=True, exist_ok=True)

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
            print(f'Training {model_name}...')

            model_save_path = models_dir / f'{model_name}_model.pkl'

            result = self.train_model(
                training_data=training_data,
                config=config,
                model_save_path=str(model_save_path),
            )

            results[model_name] = result
            print(f"{model_name} accuracy: {result['metrics']['accuracy']:.4f}")

        return results


class CrossValidationTrainer:
    """Cross-validation trainer for robust model evaluation"""

    def __init__(self, data_dir: str = './data'):
        self.data_dir = Path(data_dir)
        self.data_generator = TrainingDataGenerator()

    def time_series_cv(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
        n_splits: int = 5,
        config: MLModelConfig = None,
    ) -> dict:
        """
        Perform time series cross-validation

        Args:
            ticker: Stock ticker symbol
            start_date: Start date
            end_date: End date
            n_splits: Number of CV splits
            config: Model configuration

        Returns:
            Cross-validation results
        """
        if config is None:
            config = MLModelConfig(model_type='random_forest')

        # Prepare all data
        trainer = ModelTrainer(str(self.data_dir))
        all_training_data = trainer.prepare_training_data(ticker, start_date, end_date)

        # Split data for time series CV
        split_size = len(all_training_data) // n_splits
        cv_results = []

        for i in range(n_splits):
            # Define train/test split
            test_start = i * split_size
            test_end = (
                (i + 1) * split_size if i < n_splits - 1 else len(all_training_data)
            )

            train_data = all_training_data[:test_start] + all_training_data[test_end:]
            test_data = all_training_data[test_start:test_end]

            if len(train_data) < 50:  # Skip if too little training data
                continue

            # Train model
            model = create_ml_model(config)
            train_metrics = model.train(train_data)

            # Evaluate on test set
            correct_predictions = 0
            total_predictions = 0

            for price_history, true_label in test_data:
                prediction = model.should_buy(price_history)
                if prediction == true_label:
                    correct_predictions += 1
                total_predictions += 1

            test_accuracy = (
                correct_predictions / total_predictions if total_predictions > 0 else 0
            )

            cv_results.append(
                {
                    'fold': i + 1,
                    'train_accuracy': train_metrics['accuracy'],
                    'test_accuracy': test_accuracy,
                    'train_samples': len(train_data),
                    'test_samples': len(test_data),
                }
            )

        return {
            'cv_results': cv_results,
            'mean_test_accuracy': np.mean([r['test_accuracy'] for r in cv_results]),
            'std_test_accuracy': np.std([r['test_accuracy'] for r in cv_results]),
            'config': config,
        }

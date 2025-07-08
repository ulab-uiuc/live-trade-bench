"""
Rule-based trading models
"""

from trading_bench.core.base import BaseModel, ModelConfig


class RuleBasedConfig(ModelConfig):
    """
    Configuration for rule-based models.
    """

    def __init__(self, rule_type: str = 'average', threshold: float = 0.0):
        """
        Initialize rule-based model configuration.

        Args:
            rule_type: Type of rule ("average", "momentum", "mean_reversion")
            threshold: Threshold for the rule
        """
        self.rule_type = rule_type
        self.threshold = threshold

    def validate(self) -> bool:
        """Validate the configuration."""
        valid_rules = ['average', 'momentum', 'mean_reversion']
        return self.rule_type in valid_rules and isinstance(self.threshold, int | float)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {'rule_type': self.rule_type, 'threshold': self.threshold}


class RuleBasedModel(BaseModel):
    """
    A simple rule-based model that implements various trading rules.

    This is a baseline model for comparison with more sophisticated approaches.
    """

    def __init__(self, config: RuleBasedConfig = None):
        """
        Initialize the rule-based model.

        Args:
            config: Configuration for the rule-based model
        """
        if config is None:
            config = RuleBasedConfig()
        super().__init__(config)
        self.is_trained = True  # Rule-based models don't need training

    def should_buy(self, price_history: list[float]) -> bool:
        """
        Apply the configured rule to determine buy signal.

        Args:
            price_history: List of historical prices

        Returns:
            True if rule signals buy, False otherwise
        """
        if not price_history:
            return False

        if self.config.rule_type == 'average':
            return self._average_rule(price_history)
        elif self.config.rule_type == 'momentum':
            return self._momentum_rule(price_history)
        elif self.config.rule_type == 'mean_reversion':
            return self._mean_reversion_rule(price_history)
        else:
            return False

    def _average_rule(self, price_history: list[float]) -> bool:
        """Buy when current price is below historical average."""
        avg_price = sum(price_history) / len(price_history)
        return price_history[-1] < avg_price + self.config.threshold

    def _momentum_rule(self, price_history: list[float]) -> bool:
        """Buy when price momentum is positive."""
        if len(price_history) < 2:
            return False
        momentum = (price_history[-1] - price_history[-2]) / price_history[-2]
        return momentum > self.config.threshold

    def _mean_reversion_rule(self, price_history: list[float]) -> bool:
        """Buy when price is significantly below moving average."""
        if len(price_history) < 10:
            return False
        moving_avg = sum(price_history[-10:]) / 10
        deviation = (price_history[-1] - moving_avg) / moving_avg
        return deviation < -self.config.threshold

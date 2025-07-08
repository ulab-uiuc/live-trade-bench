# Quantitative Backtesting Metrics System Guide

## Overview

This project's quantitative backtesting metrics system provides comprehensive trading strategy evaluation indicators, including basic statistics, risk metrics, return metrics, trading statistics, time metrics, and advanced metrics across six major categories.

## Metric Categories

### 1. Basic Statistical Indicators

- **total_trades**: Total number of trades
- **winning_trades**: Number of profitable trades
- **losing_trades**: Number of losing trades
- **win_rate**: Win rate (profitable trades / total trades)
- **avg_return**: Average return rate
- **max_return**: Maximum single trade return
- **min_return**: Maximum single trade loss
- **best_trade**: Best trade return
- **worst_trade**: Worst trade loss

### 2. Return Metrics

- **total_return**: Total return rate
- **avg_win**: Average win
- **avg_loss**: Average loss
- **profit_factor**: Profit factor (total profit / total loss)
- **final_equity**: Final equity

### 3. Risk Metrics

- **volatility**: Volatility (return rate standard deviation)
- **max_drawdown**: Maximum drawdown
- **sharpe_ratio**: Sharpe ratio (return / risk)
- **sortino_ratio**: Sortino ratio (only considering downside risk)
- **calmar_ratio**: Calmar ratio (annualized return / max drawdown)
- **var_95**: Value at Risk at 95% confidence level
- **var_99**: Value at Risk at 99% confidence level

### 4. Trading Statistics

- **consecutive_wins**: Maximum consecutive wins
- **consecutive_losses**: Maximum consecutive losses
- **avg_trade_duration**: Average trade duration

### 5. Time Metrics

- **total_days**: Total trading days
- **avg_trades_per_day**: Average trades per day

### 6. Advanced Metrics

- **avg_equity_curve**: Average equity curve value
- **equity_curve_volatility**: Equity curve volatility

## Usage

### Basic Usage

```python
from trading_bench.bench import SimBench
from trading_bench.model_wrapper import RuleBasedModel

# Create backtesting instance
model = RuleBasedModel()
bench = SimBench(
    ticker='AAPL',
    start_date='2024-01-01',
    end_date='2024-06-01',
    data_dir='./data',
    model=model,
    eval_delay=5,
    resolution='D'
)

# Run backtesting and get metrics
summary = bench.run()

# Access various metrics
print(f"Win Rate: {summary['win_rate']:.2%}")
print(f"Sharpe Ratio: {summary['sharpe_ratio']:.4f}")
print(f"Max Drawdown: {summary['max_drawdown']:.2%}")
```

### Get Detailed Trade Records

```python
# Get detailed information for all trades
trade_details = bench.logger.get_trade_details()

for trade in trade_details:
    print(f"Entry Time: {trade['entry_time']}")
    print(f"Entry Price: ${trade['entry_price']:.2f}")
    print(f"Exit Time: {trade['exit_time']}")
    print(f"Exit Price: ${trade['exit_price']:.2f}")
    print(f"Return: {trade['return_pct']:.2%}")
    print(f"Trade Duration: {trade['trade_duration']}")
    print(f"High During Trade: ${trade['high_during_trade']:.2f}")
    print(f"Low During Trade: ${trade['low_during_trade']:.2f}")
```

### Get Equity Curve

```python
# Get equity curve data
equity_curve = bench.logger.get_equity_curve()
print(f"Equity Curve Points: {len(equity_curve)}")
print(f"Final Equity: {equity_curve[-1]:.4f}")
```

## Metric Explanations

### Key Risk Metrics

1. **Sharpe Ratio**

   - Measures risk-adjusted returns
   - Higher is better, typically >1 is good

2. **Maximum Drawdown**

   - Maximum drawdown
   - Lower is better, typically <20% is acceptable

3. **VaR (Value at Risk)**
   - Maximum possible loss at given confidence level
   - VaR(95%) means 95% probability that loss won't exceed this value

### Key Return Metrics

1. **Profit Factor**

   - Total profit / total loss
   - > 1 is profitable, >2 is good

2. **Win Rate**
   - Proportion of profitable trades to total trades
   - Typically >50% is good

## Test Commands

```bash
# Run metrics system test
make test-metrics

# Or run directly
python examples/test_metrics.py
```

## Extending Metrics

To add new metrics, you can add new calculation methods in the `MetricsLogger` class and call them in the `summary()` method.

For example, adding annualized return:

```python
def _annualized_return(self) -> float:
    """Calculate annualized return rate"""
    if not self.trades:
        return 0.0

    total_days = (self.trades[-1].exit_time - self.trades[0].entry_time).days
    if total_days == 0:
        return 0.0

    total_return = self.current_equity - 1.0
    annualized = (1 + total_return) ** (365 / total_days) - 1
    return annualized
```

## Notes

1. All return rates are expressed as decimals (e.g., 0.05 represents 5%)
2. Equity curve starts from 1.0, representing 100% initial capital
3. Time calculations are based on trading days, excluding weekends and holidays
4. Risk metrics assume risk-free rate of 0

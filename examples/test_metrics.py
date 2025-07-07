"""
Test the new quantitative metrics system
Demonstrate calculation of various backtesting metrics
"""

from trading_bench import RuleBasedModel, SimBench
from trading_bench.utils import setup_logging


def test_metrics() -> None:
    """Test the new quantitative metrics system"""
    setup_logging()

    print('🚀 Starting quantitative metrics system test...')

    # Create backtesting instance
    model = RuleBasedModel()
    bench = SimBench(
        ticker='AAPL',
        start_date='2025-01-01',
        end_date='2025-06-01',
        data_dir='./data',
        model=model,
        eval_delay=5,
        resolution='D',
    )

    # Run backtesting
    print('📊 Running backtesting...')
    summary = bench.run()

    # Print detailed metrics report
    print('\n' + '=' * 60)
    print('📈 Quantitative Backtesting Metrics Report')
    print('=' * 60)

    # Basic statistical indicators
    print('\n📊 Basic Statistical Indicators:')
    print(f"  Total Trades: {summary['total_trades']}")
    print(f"  Winning Trades: {summary['winning_trades']}")
    print(f"  Losing Trades: {summary['losing_trades']}")
    print(f"  Win Rate: {summary['win_rate']:.2%}")
    print(f"  Average Return: {summary['avg_return']:.2%}")
    print(f"  Max Single Trade Return: {summary['max_return']:.2%}")
    print(f"  Min Single Trade Return: {summary['min_return']:.2%}")

    # Return metrics
    print('\n💰 Return Metrics:')
    print(f"  Total Return: {summary['total_return']:.2%}")
    print(f"  Average Win: {summary['avg_win']:.2%}")
    print(f"  Average Loss: {summary['avg_loss']:.2%}")
    print(f"  Profit Factor: {summary['profit_factor']:.2f}")
    print(f"  Final Equity: {summary['final_equity']:.4f}")

    # Risk metrics
    print('\n⚠️ Risk Metrics:')
    print(f"  Volatility: {summary['volatility']:.2%}")
    print(f"  Max Drawdown: {summary['max_drawdown']:.2%}")
    print(f"  Sharpe Ratio: {summary['sharpe_ratio']:.4f}")
    print(f"  Sortino Ratio: {summary['sortino_ratio']:.4f}")
    print(f"  Calmar Ratio: {summary['calmar_ratio']:.4f}")
    print(f"  VaR(95%): {summary['var_95']:.2%}")
    print(f"  VaR(99%): {summary['var_99']:.2%}")

    # Trading statistics
    print('\n📈 Trading Statistics:')
    print(f"  Max Consecutive Wins: {summary['consecutive_wins']}")
    print(f"  Max Consecutive Losses: {summary['consecutive_losses']}")
    print(f"  Average Trade Duration: {summary['avg_trade_duration']:.1f} days")

    # Time metrics
    print('\n⏰ Time Metrics:')
    print(f"  Total Trading Days: {summary['total_days']}")
    print(f"  Average Trades per Day: {summary['avg_trades_per_day']:.2f}")

    # Advanced metrics
    print('\n🔬 Advanced Metrics:')
    print(f"  Average Equity Curve: {summary['avg_equity_curve']:.4f}")
    print(f"  Equity Curve Volatility: {summary['equity_curve_volatility']:.2%}")

    print('\n' + '=' * 60)

    # Get detailed trade records
    trade_details = bench.logger.get_trade_details()
    print('\n📋 Detailed Trade Records (First 5):')
    for i, trade in enumerate(trade_details[:5]):
        print(f'  Trade {i+1}:')
        print(f"    Entry Time: {trade['entry_time']}")
        print(f"    Entry Price: ${trade['entry_price']:.2f}")
        print(f"    Exit Time: {trade['exit_time']}")
        print(f"    Exit Price: ${trade['exit_price']:.2f}")
        print(f"    Return: {trade['return_pct']:.2%}")
        print(f"    Trade Duration: {trade['trade_duration']}")
        print(f"    High During Trade: ${trade['high_during_trade']:.2f}")
        print(f"    Low During Trade: ${trade['low_during_trade']:.2f}")
        print()

    # Get equity curve
    equity_curve = bench.logger.get_equity_curve()
    print('📈 Equity Curve Statistics:')
    print(f'  Equity Curve Points: {len(equity_curve)}')
    print(f'  Final Equity: {equity_curve[-1]:.4f}')
    print(f'  Highest Equity: {max(equity_curve):.4f}')
    print(f'  Lowest Equity: {min(equity_curve):.4f}')

    print('\n✅ Quantitative metrics system test completed!')


if __name__ == '__main__':
    test_metrics()

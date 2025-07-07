#!/usr/bin/env python3
"""
Test the backtesting visualization system
Demonstrate chart generation capabilities
"""

from trading_bench import SimBench, RuleBasedModel
from trading_bench.utils import setup_logging


def test_visualization() -> None:
    """Test the backtesting visualization system"""
    setup_logging()

    print('🚀 Starting backtesting visualization test...')

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

    # Generate charts
    print('📈 Generating charts...')
    chart_paths = bench.generate_charts(save=True)

    # Print chart information
    print('\n' + '=' * 60)
    print('📊 Generated Charts')
    print('=' * 60)

    for chart_type, filepath in chart_paths.items():
        if filepath:
            print(f'✅ {chart_type}: {filepath}')
        else:
            print(f'❌ {chart_type}: No data available')

    print('\n' + '=' * 60)
    print('📈 Chart Descriptions:')
    print('=' * 60)

    print("""
📊 Chart Types Generated:

1. Equity Curve - Shows the growth of your portfolio over time
2. Drawdown Analysis - Visualizes periods of decline from peaks
3. Trade Distribution - Histogram and box plot of trade returns
4. Monthly Returns - Bar chart showing performance by month
5. Cumulative Returns - Total return progression over trades
6. Trade Timeline - Visual timeline of entry/exit points
7. Dashboard - Comprehensive overview with all key metrics

All charts are saved in the './charts' directory with high resolution (300 DPI).
    """)

    # Print summary statistics
    print('\n📊 Key Performance Metrics:')
    print(f"  Total Return: {summary['total_return']:.2%}")
    print(f"  Sharpe Ratio: {summary['sharpe_ratio']:.4f}")
    print(f"  Max Drawdown: {summary['max_drawdown']:.2%}")
    print(f"  Win Rate: {summary['win_rate']:.2%}")
    print(f"  Total Trades: {summary['total_trades']}")

    print('\n✅ Visualization test completed!')
    print("📁 Check the './charts' directory for generated images.")


if __name__ == '__main__':
    test_visualization()

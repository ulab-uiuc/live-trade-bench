import argparse

from trading_bench.bench import SimBench
from trading_bench.model_wrapper import RuleBasedModel
from trading_bench.utils import setup_logging


def main():
    setup_logging()
    parser = argparse.ArgumentParser(
        description='Run the simulated trading bench with Finnhub data crawler'
    )
    parser.add_argument('--ticker', default='AAPL', help='Stock ticker symbol')
    parser.add_argument('--start_date', default='2024-01-01', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end_date', default='2024-06-01', help='End date (YYYY-MM-DD)')
    parser.add_argument(
        '--data_dir', default='./data', help='Root directory where data is stored'
    )
    parser.add_argument(
        '--eval_delay', type=int, default=5, help='Evaluation delay in data points'
    )
    parser.add_argument(
        '--resolution',
        choices=['1', '5', '15', '30', '60', 'D', 'W', 'M'],
        default='D',
        help="Finnhub data resolution (e.g., '1','5','15','30','60','D','W','M')",
    )

    args = parser.parse_args()

    model = RuleBasedModel()
    bench = SimBench(
        ticker=args.ticker,
        start_date=args.start_date,
        end_date=args.end_date,
        data_dir=args.data_dir,
        model=model,
        eval_delay=args.eval_delay,
        resolution=args.resolution,
    )
    summary = bench.run()

    print('Performance Summary:')
    for key, value in summary.items():
        if isinstance(value, float):
            print(f'{key}: {value:.4f}')
        else:
            print(f'{key}: {value}')


if __name__ == '__main__':
    main()

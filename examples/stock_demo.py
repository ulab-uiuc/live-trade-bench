#!/usr/bin/env python3
"""
Example script demonstrating how to use the price data fetching functionality.
"""

from trading_bench.data_fetchers.stock_fetcher import fetch_price_data


def main():
    """Demonstrate price data fetching functionality with retry logic."""

    # Example: Fetch Apple stock price data for the last month
    ticker = 'AAPL'
    start_date = '2024-01-01'
    end_date = '2024-01-31'
    resolution = 'D'  # Daily data

    print(f'Fetching price data for {ticker}')
    print(f'Date range: {start_date} to {end_date}')
    print(f'Resolution: {resolution}')
    print('-' * 50)

    try:
        price_data = fetch_price_data(ticker, start_date, end_date, resolution)

        print(f'Successfully fetched {len(price_data)} days of price data:')
        print()

        # Display first few days of data
        for _i, (date, data) in enumerate(list(price_data.items())[:5]):
            print(f'Date: {date}')
            print(f"  Open:  ${data['open']:.2f}")
            print(f"  High:  ${data['high']:.2f}")
            print(f"  Low:   ${data['low']:.2f}")
            print(f"  Close: ${data['close']:.2f}")
            print(f"  Volume: {data['volume']:,}")
            print()

        if len(price_data) > 5:
            print(f'... and {len(price_data) - 5} more days of data')

    except Exception as e:
        print(f'Error fetching price data: {e}')
        print('Note: The function will automatically retry up to 3 times on failure')


def demonstrate_retry():
    """Demonstrate the retry functionality with a potentially problematic request."""

    print('\n' + '=' * 60)
    print('Demonstrating retry functionality...')
    print('=' * 60)

    # Try to fetch data for a potentially problematic ticker
    ticker = 'INVALID_TICKER'
    start_date = '2024-01-01'
    end_date = '2024-01-31'

    print(f'Attempting to fetch data for invalid ticker: {ticker}')
    print('This should demonstrate the retry logic...')

    try:
        fetch_price_data(ticker, start_date, end_date)
        print('Unexpected success!')
    except Exception as e:
        print(f'Expected error after retries: {e}')
        print('The function attempted to retry the request multiple times')


if __name__ == '__main__':
    main()
    demonstrate_retry()

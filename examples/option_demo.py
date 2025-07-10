#!/usr/bin/env python3
"""
Example script demonstrating how to use the option data fetching functionality.
"""

from datetime import datetime

from trading_bench.fetchers.option_fetcher import (
    calculate_option_greeks,
    fetch_option_chain,
    fetch_option_data,
    fetch_option_expirations,
    fetch_option_historical_data,
)


def main():
    """Demonstrate option data fetching functionality."""

    ticker = 'AAPL'

    print(f'Fetching option data for {ticker}')
    print('=' * 60)

    try:
        # 1. Get available expiration dates
        print('1. Available expiration dates:')
        expirations = fetch_option_expirations(ticker)
        print(f'   Found {len(expirations)} expiration dates')
        for i, exp in enumerate(expirations[:5]):  # Show first 5
            print(f'   {i+1}. {exp}')
        if len(expirations) > 5:
            print(f'   ... and {len(expirations) - 5} more')
        print()

        # 2. Get option chain for nearest expiration
        print('2. Option chain for nearest expiration:')
        option_chain = fetch_option_chain(ticker)
        print(f"   Expiration: {option_chain['expiration']}")
        print(f"   Underlying Price: ${option_chain['underlying_price']:.2f}")
        print(f"   Calls available: {len(option_chain['calls'])}")
        print(f"   Puts available: {len(option_chain['puts'])}")
        print()

        # 3. Show sample call options
        print('3. Sample call options (first 5):')
        for i, call in enumerate(option_chain['calls'][:5]):
            print(
                f"   {i+1}. Strike: ${call['strike']:.2f}, "
                f"Bid: ${call['bid']:.2f}, Ask: ${call['ask']:.2f}, "
                f"Volume: {call['volume']}"
            )
        print()

        # 4. Show sample put options
        print('4. Sample put options (first 5):')
        for i, put in enumerate(option_chain['puts'][:5]):
            print(
                f"   {i+1}. Strike: ${put['strike']:.2f}, "
                f"Bid: ${put['bid']:.2f}, Ask: ${put['ask']:.2f}, "
                f"Volume: {put['volume']}"
            )
        print()

        # 5. Filter options by strike range
        print('5. Options within strike range (near-the-money):')
        underlying_price = option_chain['underlying_price']
        min_strike = underlying_price * 0.9
        max_strike = underlying_price * 1.1

        filtered_options = fetch_option_data(
            ticker,
            option_chain['expiration'],
            option_type='both',
            min_strike=min_strike,
            max_strike=max_strike,
        )

        print(f'   Strike range: ${min_strike:.2f} - ${max_strike:.2f}')
        print(f"   Calls in range: {len(filtered_options['calls'])}")
        print(f"   Puts in range: {len(filtered_options['puts'])}")
        print()

        # 6. Calculate Greeks for a sample option
        print('6. Greeks calculation example:')
        sample_call = (
            filtered_options['calls'][0] if filtered_options['calls'] else None
        )
        if sample_call:
            # Calculate time to expiry
            exp_date = datetime.strptime(option_chain['expiration'], '%Y-%m-%d')
            current_date = datetime.now()
            time_to_expiry = (exp_date - current_date).days / 365.0

            greeks = calculate_option_greeks(
                underlying_price=underlying_price,
                strike=sample_call['strike'],
                time_to_expiry=time_to_expiry,
                risk_free_rate=0.05,  # 5% risk-free rate
                volatility=0.3,  # 30% volatility
                option_type='call',
            )

            print('   Sample Call Option:')
            print(f"     Strike: ${sample_call['strike']:.2f}")
            print(f'     Time to Expiry: {time_to_expiry:.2f} years')
            print(f"     Delta: {greeks['delta']:.4f}")
            print(f"     Gamma: {greeks['gamma']:.4f}")
            print(f"     Theta: {greeks['theta']:.4f}")
            print(f"     Vega: {greeks['vega']:.4f}")
            print(f"     Rho: {greeks['rho']:.4f}")

    except Exception as e:
        print(f'Error: {e}')


def demonstrate_historical_data():
    """Demonstrate historical option data fetching."""

    print('\n' + '=' * 60)
    print('Historical Option Data Example')
    print('=' * 60)

    ticker = 'AAPL'
    expiration_date = '2024-01-19'  # Example expiration
    strike = 150.0
    option_type = 'call'
    start_date = '2024-01-01'
    end_date = '2024-01-15'

    try:
        print(f'Fetching historical data for {ticker} {strike} {option_type}')
        print(f'Expiration: {expiration_date}')
        print(f'Date range: {start_date} to {end_date}')
        print()

        historical_data = fetch_option_historical_data(
            ticker, expiration_date, strike, option_type, start_date, end_date
        )

        print(f"Option Symbol: {historical_data['option_symbol']}")
        print(f"Price data points: {len(historical_data['price_data'])}")
        print()

        # Show first few days of data
        print('Sample price data:')
        for i, (date, data) in enumerate(
            list(historical_data['price_data'].items())[:3]
        ):
            print(
                f"  {date}: Open=${data['open']:.2f}, "
                f"Close=${data['close']:.2f}, Volume={data['volume']}"
            )

    except Exception as e:
        print(f'Error fetching historical data: {e}')


if __name__ == '__main__':
    main()
    demonstrate_historical_data()

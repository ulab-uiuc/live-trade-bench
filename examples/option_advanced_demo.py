#!/usr/bin/env python3
"""
Advanced example script demonstrating the new option data fetching functionality.
"""

from datetime import datetime, timedelta

from trading_bench.fetchers.option_fetcher import (
    calculate_implied_volatility,
    calculate_option_greeks,
    fetch_option_chain,
    fetch_option_expirations,
    fetch_option_historical_data,
    get_atm_options,
    get_option_chain_summary,
)


def main():
    """Demonstrate advanced option data fetching functionality."""

    ticker = 'AAPL'

    print('Advanced Option Data Fetching Demo')
    print('=' * 60)

    try:
        # 1. Get option chain summary
        print('1. Option Chain Summary:')
        summary = get_option_chain_summary(ticker)

        print(f"   Ticker: {summary['ticker']}")
        print(f"   Expiration: {summary['expiration']}")
        print(f"   Underlying Price: ${summary['underlying_price']:.2f}")
        print(f"   Total Options: {summary['total_options']}")
        print(f"   Put/Call Ratio: {summary['put_call_ratio']:.2f}")
        print()

        # 2. Get ATM options
        print('2. At-The-Money Options:')
        atm_options = get_atm_options(ticker, summary['expiration'])

        print(f"   Current Price: ${atm_options['current_price']:.2f}")
        print(
            f"   Strike Range: ${atm_options['strike_range']['min']:.2f} - ${atm_options['strike_range']['max']:.2f}"
        )
        print(f"   Range: ±{atm_options['strike_range']['range_percent']:.1f}%")
        print(f"   ATM Calls: {len(atm_options['calls'])}")
        print(f"   ATM Puts: {len(atm_options['puts'])}")
        print()

        # 3. Calculate implied volatility for a sample option
        if atm_options['calls']:
            sample_call = atm_options['calls'][0]
            print('3. Implied Volatility Calculation:')
            print(
                f"   Sample Call: Strike ${sample_call['strike']:.2f}, Bid ${sample_call['bid']:.2f}, Ask ${sample_call['ask']:.2f}"
            )

            # Calculate time to expiry
            exp_date = datetime.strptime(summary['expiration'], '%Y-%m-%d')
            current_date = datetime.now()
            time_to_expiry = (exp_date - current_date).days / 365.0

            # Use mid-price for implied volatility calculation
            mid_price = (sample_call['bid'] + sample_call['ask']) / 2

            try:
                implied_vol = calculate_implied_volatility(
                    option_price=mid_price,
                    underlying_price=atm_options['current_price'],
                    strike=sample_call['strike'],
                    time_to_expiry=time_to_expiry,
                    risk_free_rate=0.05,  # 5% risk-free rate
                    option_type='call',
                )
                print(f'   Implied Volatility: {implied_vol:.1%}')
            except Exception as e:
                print(f'   Error calculating implied volatility: {e}')
            print()

        # 4. Advanced Greeks calculation with implied volatility
        print('4. Advanced Greeks Calculation:')
        if 'implied_vol' in locals():
            greeks = calculate_option_greeks(
                underlying_price=atm_options['current_price'],
                strike=sample_call['strike'],
                time_to_expiry=time_to_expiry,
                risk_free_rate=0.05,
                volatility=implied_vol,
                option_type='call',
            )

            print(f"   Delta: {greeks['delta']:.4f}")
            print(f"   Gamma: {greeks['gamma']:.6f}")
            print(f"   Theta: {greeks['theta']:.4f}")
            print(f"   Vega: {greeks['vega']:.4f}")
            print(f"   Rho: {greeks['rho']:.4f}")
            print()

        # 5. Compare calls vs puts
        print('5. Calls vs Puts Analysis:')
        calls = atm_options['calls']
        puts = atm_options['puts']

        if calls and puts:
            avg_call_volume = sum(call['volume'] for call in calls) / len(calls)
            avg_put_volume = sum(put['volume'] for put in puts) / len(puts)

            print(f'   Average Call Volume: {avg_call_volume:.0f}')
            print(f'   Average Put Volume: {avg_put_volume:.0f}')
            print(f'   Put/Call Volume Ratio: {avg_put_volume/avg_call_volume:.2f}')

            # Find most liquid options
            most_liquid_call = max(calls, key=lambda x: x['volume'])
            most_liquid_put = max(puts, key=lambda x: x['volume'])

            print(
                f"   Most Liquid Call: Strike ${most_liquid_call['strike']:.2f}, Volume {most_liquid_call['volume']}"
            )
            print(
                f"   Most Liquid Put: Strike ${most_liquid_put['strike']:.2f}, Volume {most_liquid_put['volume']}"
            )
            print()

        # 6. Historical option data
        print('6. Historical Option Data:')
        if atm_options['calls']:
            sample_call = atm_options['calls'][0]
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            end_date = datetime.now().strftime('%Y-%m-%d')

            try:
                historical_data = fetch_option_historical_data(
                    ticker=ticker,
                    expiration_date=summary['expiration'],
                    strike=sample_call['strike'],
                    option_type='call',
                    start_date=start_date,
                    end_date=end_date,
                )

                print(f"   Option Symbol: {historical_data['option_symbol']}")
                print(f"   Data Points: {len(historical_data['price_data'])}")

                if historical_data['price_data']:
                    latest_date = max(historical_data['price_data'].keys())
                    latest_data = historical_data['price_data'][latest_date]
                    print(f"   Latest Close: ${latest_data['close']:.2f}")
                    print(f"   Latest Volume: {latest_data['volume']}")

            except Exception as e:
                print(f'   Error fetching historical data: {e}')
            print()

    except Exception as e:
        print(f'Error: {e}')


def demonstrate_volatility_surface():
    """Demonstrate implied volatility surface calculation."""

    print('\n' + '=' * 60)
    print('Implied Volatility Surface Demo')
    print('=' * 60)

    ticker = 'AAPL'

    try:
        # Get available expirations
        expirations = fetch_option_expirations(ticker)
        print(f'Available expirations: {len(expirations)}')

        # Focus on first few expirations
        for i, expiration in enumerate(expirations[:3]):
            print(f'\nExpiration {i+1}: {expiration}')

            # Get ATM options for this expiration
            atm_options = get_atm_options(ticker, expiration)

            if atm_options['calls'] and atm_options['puts']:
                # Calculate time to expiry
                exp_date = datetime.strptime(expiration, '%Y-%m-%d')
                current_date = datetime.now()
                time_to_expiry = (exp_date - current_date).days / 365.0

                print(f'   Time to Expiry: {time_to_expiry:.2f} years')
                print(f"   Underlying Price: ${atm_options['current_price']:.2f}")

                # Calculate implied volatility for a few strikes
                for option in atm_options['calls'][:3]:
                    mid_price = (option['bid'] + option['ask']) / 2

                    try:
                        implied_vol = calculate_implied_volatility(
                            option_price=mid_price,
                            underlying_price=atm_options['current_price'],
                            strike=option['strike'],
                            time_to_expiry=time_to_expiry,
                            risk_free_rate=0.05,
                            option_type='call',
                        )
                        print(
                            f"   Strike ${option['strike']:.2f}: IV = {implied_vol:.1%}"
                        )
                    except Exception:
                        print(
                            f"   Strike ${option['strike']:.2f}: Error calculating IV"
                        )

    except Exception as e:
        print(f'Error in volatility surface demo: {e}')


def demonstrate_option_strategies():
    """Demonstrate option strategy analysis."""

    print('\n' + '=' * 60)
    print('Option Strategy Demo')
    print('=' * 60)

    ticker = 'AAPL'

    try:
        # Get option chain
        option_chain = fetch_option_chain(ticker)
        underlying_price = option_chain['underlying_price']

        print(f'Underlying Price: ${underlying_price:.2f}')
        print(f"Expiration: {option_chain['expiration']}")

        # Find options for a straddle strategy (ATM call and put)
        calls = option_chain['calls']
        puts = option_chain['puts']

        # Find ATM options (closest to current price)
        atm_call = min(calls, key=lambda x: abs(x['strike'] - underlying_price))
        atm_put = min(puts, key=lambda x: abs(x['strike'] - underlying_price))

        print('\nStraddle Strategy:')
        print(
            f"   Call: Strike ${atm_call['strike']:.2f}, Bid ${atm_call['bid']:.2f}, Ask ${atm_call['ask']:.2f}"
        )
        print(
            f"   Put: Strike ${atm_put['strike']:.2f}, Bid ${atm_put['bid']:.2f}, Ask ${atm_put['ask']:.2f}"
        )

        # Calculate straddle cost
        straddle_cost = atm_call['ask'] + atm_put['ask']
        print(f'   Straddle Cost: ${straddle_cost:.2f}')

        # Calculate break-even points
        break_even_up = atm_call['strike'] + straddle_cost
        break_even_down = atm_put['strike'] - straddle_cost
        print(f'   Break-even Up: ${break_even_up:.2f}')
        print(f'   Break-even Down: ${break_even_down:.2f}')

    except Exception as e:
        print(f'Error in option strategy demo: {e}')


if __name__ == '__main__':
    main()
    demonstrate_volatility_surface()
    demonstrate_option_strategies()

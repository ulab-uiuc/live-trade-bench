# Example usage: fetch last week's daily prices for Apple

from datetime import datetime, timedelta

from trading_bench.fetchers.stock_fetcher import fetch_stock_data


def main():
    ticker = 'AAPL'
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')

    print(
        f'\n📈 Fetching daily OHLCV data for {ticker} from {start_str} to {end_str}...\n'
    )

    try:
        price_data = fetch_stock_data(
            ticker=ticker, start_date=start_str, end_date=end_str, resolution='D'
        )

        if not price_data:
            print('⚠️ No data returned.')
            return

        # Sort dates ascending
        sorted_dates = sorted(price_data.keys())
        print(f'✅ Retrieved {len(sorted_dates)} records:\n')

        for date in sorted_dates:
            ohlcv = price_data[date]

            def fmt(x):
                if isinstance(x, (int, float)):
                    return f'{x:<6.2f}'
                return f'{str(x):<6}'

            open_price = fmt(ohlcv.get('open', 'N/A'))
            high_price = fmt(ohlcv.get('high', 'N/A'))
            low_price = fmt(ohlcv.get('low', 'N/A'))
            close_price = fmt(ohlcv.get('close', 'N/A'))
            volume = ohlcv.get('volume', 'N/A')

            print(
                f'{date:<10} | '
                f'Open: {open_price} '
                f'High: {high_price} '
                f'Low: {low_price} '
                f'Close: {close_price} '
                f'Volume: {volume}'
            )

        print('\n🎯 Data fetch complete.\n')

    except Exception as e:
        print(f'❌ Error fetching data: {e}')


if __name__ == '__main__':
    main()

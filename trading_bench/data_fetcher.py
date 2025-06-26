import json
import os
import time

import yfinance as yf


def fetch_price_data(
    ticker: str, start_date: str, end_date: str, data_dir: str, resolution: str = 'D'
) -> None:
    """
    Fetches historical OHLCV price data for a ticker via yfinance and saves it as formatted JSON.
    Args:
        ticker:     Stock ticker symbol.
        start_date: YYYY-MM-DD
        end_date:   YYYY-MM-DD
        data_dir:   Root data directory where 'yfinance_data/price_data' will live.
        resolution: '1', '5', '15', '30', '60', 'D', 'W', 'M'
    """
    # map your resolution codes to yfinance intervals
    interval_map = {
        '1': '1m',
        '5': '5m',
        '15': '15m',
        '30': '30m',
        '60': '60m',
        'D': '1d',
        'W': '1wk',
        'M': '1mo',
    }
    interval = interval_map.get(resolution.upper(), '1d')

    # download data
    df = yf.download(
        tickers=ticker,
        start=start_date,
        end=end_date,
        interval=interval,
        progress=False,
    )

    if df.empty:
        raise RuntimeError(
            f'No data returned for {ticker} {start_date}→{end_date} @ {interval}'
        )

    # Build date-indexed dict
    data = {}
    for idx, row in df.iterrows():
        # idx is a pandas.Timestamp
        date_str = idx.strftime('%Y-%m-%d')
        data[date_str] = {
            'open': float(row['Open']),
            'high': float(row['High']),
            'low': float(row['Low']),
            'close': float(row['Close']),
            'volume': int(row['Volume']),
        }

    # Ensure target directory exists
    out_dir = os.path.join(data_dir, 'yfinance_data', 'price_data')
    os.makedirs(out_dir, exist_ok=True)

    out_path = os.path.join(out_dir, f'{ticker}_data_formatted.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    # be polite with any rate limits
    time.sleep(1)

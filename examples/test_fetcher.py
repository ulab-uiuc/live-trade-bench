from trading_bench.data_fetcher import fetch_price_data

data = fetch_price_data(
    ticker="AAPL",
    start_date="2025-07-01",
    end_date="2025-07-03",
    resolution="1",
)

print(data)
# Example usage: fetch last week's daily prices for Apple

import os
import sys
from pathlib import Path

from trading_bench.fetchers.stock_fetcher import fetch_stock_data
from trading_bench.model import AIStockAnalysisModel

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def main():
    ticker = "AAPL"
    start_date = "2024-01-01"
    end_date = "2024-01-31"
    resolution = "D"  # Daily data

    print(f"Fetching price data for {ticker}")
    print(f"Date range: {start_date} to {end_date}")
    print(f"Resolution: {resolution}")
    print("-" * 50)

    try:
        price_data = fetch_stock_data(ticker, start_date, end_date, resolution)

        print(f"Successfully fetched {len(price_data)} days of price data:")
        print()

        # Display first few days of data
        for i, (date, data) in enumerate(list(price_data.items())[:5]):
            print(f"Date: {date}")
            print(f"  Open:  ${data['open']:.2f}")
            print(f"  High:  ${data['high']:.2f}")
            print(f"  Low:   ${data['low']:.2f}")
            print(f"  Close: ${data['close']:.2f}")
            print(f"  Volume: {data['volume']:,}")
            print()

        if len(price_data) > 5:
            print(f"... and {len(price_data) - 5} more days of data")

    except Exception as e:
        print(f"Error fetching price data: {e}")
        print("Note: The function will automatically retry up to 3 times on failure")


def demonstrate_retry():
    """Demonstrate the retry functionality with a potentially problematic request."""

    print("\n" + "=" * 60)
    print("Demonstrating retry functionality...")
    print("=" * 60)

    # Try to fetch data for a potentially problematic ticker
    ticker = "INVALID_TICKER"
    start_date = "2024-01-01"
    end_date = "2024-01-31"

    print(f"Attempting to fetch data for invalid ticker: {ticker}")
    print("This should demonstrate the retry logic...")

    try:
        fetch_stock_data(ticker, start_date, end_date)
        print("Unexpected success!")
    except Exception as e:
        print(f"Expected error after retries: {e}")
        print("The function attempted to retry the request multiple times")


def demonstrate_ai_analysis():
    """Demonstrate AI stock analysis functionality."""

    print("\n" + "=" * 60)
    print("Demonstrating AI Stock Analysis...")
    print("=" * 60)

    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY not set. Skipping AI analysis demo.")
        print("   To enable AI analysis, set: export OPENAI_API_KEY='your-key-here'")
        return

    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    print(
        f"\n📈 Fetching daily OHLCV data for {ticker} from {start_str} to {end_str}...\n"
    )

    try:
        price_data = fetch_stock_data(
            ticker=ticker, start_date=start_str, end_date=end_str, resolution="D"
        )

        if not price_data:
            print("⚠️ No data returned.")
            return

        # Sort dates ascending
        sorted_dates = sorted(price_data.keys())
        print(f"✅ Retrieved {len(sorted_dates)} records:\n")

        for date in sorted_dates:
            ohlcv = price_data[date]

            def fmt(x):
                if isinstance(x, (int, float)):
                    return f"{x:<6.2f}"
                return f"{str(x):<6}"

            open_price = fmt(ohlcv.get("open", "N/A"))
            high_price = fmt(ohlcv.get("high", "N/A"))
            low_price = fmt(ohlcv.get("low", "N/A"))
            close_price = fmt(ohlcv.get("close", "N/A"))
            volume = ohlcv.get("volume", "N/A")

            print(
                f"{date:<10} | "
                f"Open: {open_price} "
                f"High: {high_price} "
                f"Low: {low_price} "
                f"Close: {close_price} "
                f"Volume: {volume}"
            )

        print("\n🎯 Data fetch complete.\n")

    except Exception as e:
        print(f"❌ Error fetching data: {e}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Example script demonstrating how to use the price data fetching functionality
and AI stock analysis.
"""

import os
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from trading_bench.data_fetchers.stock_fetcher import fetch_price_data
from trading_bench.model_wrapper import AIStockAnalysisModel
from trading_bench.bench import SimBench


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
        for i, (date, data) in enumerate(list(price_data.items())[:5]):
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
        price_data = fetch_price_data(ticker, start_date, end_date)
        print('Unexpected success!')
    except Exception as e:
        print(f'Expected error after retries: {e}')
        print('The function attempted to retry the request multiple times')


def demonstrate_ai_analysis():
    """Demonstrate AI stock analysis functionality."""
    
    print('\n' + '=' * 60)
    print('Demonstrating AI Stock Analysis...')
    print('=' * 60)
    
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY not set. Skipping AI analysis demo.")
        print("   To enable AI analysis, set: export OPENAI_API_KEY='your-key-here'")
        return
    
    # Use NVDA for AI analysis
    ticker = "NVDA"
    start_date = "2024-01-01"
    end_date = "2024-01-31"
    
    print(f"Fetching {ticker} data for AI analysis...")
    print(f"Date range: {start_date} to {end_date}")
    print("-" * 50)
    
    try:
        # Fetch price data
        price_data = fetch_price_data(ticker, start_date, end_date, "D")
        
        # Convert to price history list
        dates = sorted(price_data.keys())
        prices = [price_data[date]["close"] for date in dates]
        
        print(f"✓ Fetched {len(prices)} days of data")
        print(f"✓ Price range: ${min(prices):.2f} - ${max(prices):.2f}")
        print()
        
        # Initialize AI model
        print("Initializing AI Stock Analysis Model...")
        ai_model = AIStockAnalysisModel(api_key=api_key)
        print("✓ AI model initialized successfully")
        print()
        
        # Get AI prediction
        print("Getting AI prediction...")
        prediction = ai_model.get_trend_prediction(prices)
        
        print(f"🤖 AI Prediction Results:")
        print(f"   Prediction: {prediction['prediction']}")
        print(f"   Confidence: {prediction['confidence']:.2f}")
        print(f"   Reasoning: {prediction['reasoning']}")
        print(f"   Latest Price: ${prediction['latest_price']:.2f}")
        print()
        
        # Test buy signal
        should_buy = ai_model.should_buy(prices)
        print(f"📊 Trading Signal: {'🟢 BUY' if should_buy else '🔴 HOLD/SELL'}")
        print()
        
        # # Run backtesting evaluation
        # print("Running backtesting evaluation...")
        # bench = SimBench(
        #     ticker=ticker,
        #     start_date=start_date,
        #     end_date=end_date,
        #     data_dir="./data",
        #     model=ai_model,
        #     eval_delay=1,
        #     resolution="D"
        # )
        
        # results = bench.run()
        
        # print("📈 Backtesting Results:")
        # print(f"   Total Return: {results.get('total_return', 0):.2%}")
        # print(f"   Win Rate: {results.get('win_rate', 0):.2%}")
        # print(f"   Total Trades: {results.get('total_trades', 0)}")
        # print(f"   Sharpe Ratio: {results.get('sharpe_ratio', 0):.2f}")
        # print()
        
        # # Final performance score
        # performance_score = results.get('win_rate', 0) * 100
        # print(f"🎯 Final Performance Score: {performance_score:.1f}/100")
        
        # if performance_score > 60:
        #     print("🟢 EXCELLENT: AI model shows strong predictive capability!")
        # elif performance_score > 50:
        #     print("🟡 GOOD: AI model shows decent predictive capability")
        # else:
        #     print("🔴 NEEDS IMPROVEMENT: AI model needs refinement")
            
    except Exception as e:
        print(f"❌ Error in AI analysis: {e}")
        print("   Make sure your OpenAI API key is valid and you have credits")


if __name__ == '__main__':
    main()
    demonstrate_retry()
    demonstrate_ai_analysis()

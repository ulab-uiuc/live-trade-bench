import argparse
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from collections import deque

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from trading_bench.bench import SimBench
from trading_bench.data_fetchers.stock_fetcher import fetch_price_data
from trading_bench.evaluator import ReturnEvaluator
from trading_bench.model_wrapper import AIStockAnalysisModel, RuleBasedModel
from trading_bench.signal import Signal
from trading_bench.utils import setup_logging


def main() -> None:
    setup_logging()
    parser = argparse.ArgumentParser(
        description='Run the simulated trading bench with Finnhub data crawler'
    )
    parser.add_argument('--ticker', default='AAPL', help='Stock ticker symbol')
    parser.add_argument(
        '--start_date', default='2025-01-01', help='Start date (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--end_date', default='2025-06-01', help='End date (YYYY-MM-DD)'
    )
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


def ai_stock_evaluation_demo():
    """
    AI Stock Evaluation Demo:
    1. Use yesterday's data to make AI prediction
    2. Use today's data to evaluate if prediction was correct
    3. Use evaluator for trade analysis
    """
    print("\n" + "=" * 60)
    print("AI Stock Evaluation Demo")
    print("=" * 60)
    
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY not set. Using RuleBasedModel instead.")
        model = RuleBasedModel()
        print("✓ Using RuleBasedModel for demonstration")
    else:
        model = AIStockAnalysisModel(api_key=api_key)
        print("✓ Using AI model for analysis")
    
    # Configuration
    ticker = "NVDA"
    yesterday = datetime(2025, 7, 2)
    today = datetime(2025, 7, 3)
    
    print(f"\nTicker: {ticker}")
    print(f"Analysis Date: {yesterday.strftime('%Y-%m-%d')}")
    print(f"Evaluation Date: {today.strftime('%Y-%m-%d')}")
    print("-" * 50)
    
    try:
        # Step 1: Get historical data
        print("1. Fetching historical data...")
        
        historical_data = fetch_price_data(
            ticker=ticker,
            start_date=(yesterday - timedelta(days=30)).strftime('%Y-%m-%d'),
            end_date=yesterday.strftime('%Y-%m-%d'),
            resolution='D'
        )
        
        if not historical_data:
            print("❌ No historical data available")
            return
        
        dates = sorted(historical_data.keys())
        prices = [historical_data[date]["close"] for date in dates]
        yesterday_price = prices[-1]
        
        print(f"✓ Fetched {len(prices)} days of data")
        print(f"✓ Yesterday's price: ${yesterday_price:.2f}")
        
        # Step 2: Make prediction
        print("\n2. Making prediction...")
        
        if isinstance(model, AIStockAnalysisModel):
            prediction_result = model.get_trend_prediction(prices)
            should_buy = model.should_buy(prices)
            
            print(f"🤖 AI Prediction: {prediction_result['prediction']}")
            print(f"🤖 Confidence: {prediction_result['confidence']:.2f}")
            print(f"📊 Buy Signal: {'YES' if should_buy else 'NO'}")
            
        else:
            should_buy = model.should_buy(prices)
            print(f"📊 Rule-based Buy Signal: {'YES' if should_buy else 'NO'}")
        
        # Step 3: Get today's data
        print("\n3. Fetching today's data...")
        
        try:
            today_data = fetch_price_data(
                ticker=ticker,
                start_date=today.strftime('%Y-%m-%d'),
                end_date=(today + timedelta(days=1)).strftime('%Y-%m-%d'),
                resolution='D'
            )
            
            if today_data:
                today_dates = sorted(today_data.keys())
                today_price = today_data[today_dates[0]]["close"]
                print(f"✓ Today's price: ${today_price:.2f}")
            else:
                print("ℹ️  Using yesterday's data for evaluation")
                today_price = yesterday_price
                yesterday_price = prices[-2] if len(prices) > 1 else yesterday_price
                
        except Exception as e:
            print(f"ℹ️  Using yesterday's data: {e}")
            today_price = yesterday_price
            yesterday_price = prices[-2] if len(prices) > 1 else yesterday_price
        
        # Step 4: Use evaluator
        print("\n4. Using evaluator for trade analysis...")
        
        # Create signal
        signal = Signal(
            entry_time=yesterday,
            entry_price=yesterday_price,
            eval_time=today,
            ticker=ticker
        )
        
        # Create price history
        price_history = deque()
        for date_str, data in historical_data.items():
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            price_history.append((date_obj, data["close"]))
        
        if today_price != yesterday_price:
            price_history.append((today, today_price))
        
        # Use evaluator
        evaluator = ReturnEvaluator()
        trade_record = evaluator.evaluate(signal, price_history)
        
        print(f"📊 Evaluator Results:")
        print(f"   Return: {trade_record.return_pct:.4f} ({trade_record.return_pct*100:.2f}%)")
        print(f"   Duration: {trade_record.trade_duration} days")
        print(f"   High: ${trade_record.high_during_trade:.2f}")
        print(f"   Low: ${trade_record.low_during_trade:.2f}")
        
        # Step 5: Final results
        print("\n" + "=" * 60)
        print("EVALUATION RESULTS")
        print("=" * 60)
        print(f"Ticker: {ticker}")
        print(f"Yesterday: ${yesterday_price:.2f}")
        print(f"Today: ${today_price:.2f}")
        print(f"Price Change: {((today_price - yesterday_price) / yesterday_price * 100):.2f}%")
        print(f"Evaluator Return: {trade_record.return_pct*100:.2f}%")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == '__main__':
    # Run original demo
    # main()
    
    # Run AI evaluation demo
    ai_stock_evaluation_demo()

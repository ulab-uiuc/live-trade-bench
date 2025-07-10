import argparse
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from trading_bench.bench import SimBench
from trading_bench.data_fetchers.stock_fetcher import fetch_price_data
from trading_bench.evaluator import ReturnEvaluator
from trading_bench.model_wrapper import AIStockAnalysisModel, RuleBasedModel
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
    # Use dates that avoid weekends and holidays (July 4th is Independence Day)
    yesterday = datetime(2025, 7, 2)  # Analysis date (Wednesday)
    today = datetime(2025, 7, 3)      # Evaluation date (Thursday)
    
    print(f"\nTicker: {ticker}")
    print(f"Analysis Date (Yesterday): {yesterday.strftime('%Y-%m-%d')}")
    print(f"Evaluation Date (Today): {today.strftime('%Y-%m-%d')}")
    print("-" * 50)
    
    try:
        # Step 1: Get yesterday's data for prediction
        print("1. Fetching historical data for yesterday's analysis...")
        
        # Get data up to yesterday for prediction
        historical_data = fetch_price_data(
            ticker=ticker,
            start_date=(yesterday - timedelta(days=30)).strftime('%Y-%m-%d'),
            end_date=yesterday.strftime('%Y-%m-%d'),
            resolution='D'
        )
        
        if not historical_data:
            print("❌ No historical data available")
            return
        
        # Convert to price list for model
        dates = sorted(historical_data.keys())
        prices = [historical_data[date]["close"] for date in dates]
        yesterday_price = prices[-1]
        
        print(f"✓ Fetched {len(prices)} days of historical data")
        print(f"✓ Yesterday's closing price: ${yesterday_price:.2f}")
        
        # Step 2: Make prediction using yesterday's data
        print("\n2. Making AI prediction based on yesterday's data...")
        
        if isinstance(model, AIStockAnalysisModel):
            prediction_result = model.get_trend_prediction(prices)
            should_buy = model.should_buy(prices)
            
            print(f"🤖 AI Prediction: {prediction_result['prediction']}")
            print(f"🤖 Confidence: {prediction_result['confidence']:.2f}")
            print(f"🤖 Reasoning: {prediction_result['reasoning']}")
            print(f"📊 Buy Signal: {'YES' if should_buy else 'NO'}")
            
        else:
            should_buy = model.should_buy(prices)
            print(f"📊 Rule-based Buy Signal: {'YES' if should_buy else 'NO'}")
        
        # Step 3: Get today's data for evaluation
        print("\n3. Fetching today's data for evaluation...")
        day_after = today + timedelta(days=1)
        try:
            today_data = fetch_price_data(
                ticker=ticker,
                start_date=today.strftime('%Y-%m-%d'),
                end_date=day_after.strftime('%Y-%m-%d'),
                resolution='D'
            )
            
            if today_data:
                today_dates = sorted(today_data.keys())
                today_price = today_data[today_dates[0]]["close"]
                print(f"✓ Today's price: ${today_price:.2f}")
            else:
                # If today's data not available, use yesterday as "today"
                print("ℹ️  Today's data not available yet, using yesterday as evaluation")
                today_price = yesterday_price
                yesterday_price = prices[-2] if len(prices) > 1 else yesterday_price
                
        except Exception as e:
            print(f"ℹ️  Using yesterday's data for evaluation: {e}")
            today_price = yesterday_price
            yesterday_price = prices[-2] if len(prices) > 1 else yesterday_price
        
        # Step 4: Evaluate prediction accuracy
        print("\n4. Evaluating prediction accuracy...")
        
        price_change = today_price - yesterday_price
        price_change_percent = (price_change / yesterday_price) * 100 if yesterday_price > 0 else 0
        
        print(f"📈 Price Change: ${price_change:.2f} ({price_change_percent:.2f}%)")
        
        # Determine actual movement
        if price_change_percent > 1.0:
            actual_movement = "BULLISH"
            stock_went_up = True
        elif price_change_percent < -1.0:
            actual_movement = "BEARISH"
            stock_went_up = False
        else:
            actual_movement = "NEUTRAL"
            stock_went_up = abs(price_change_percent) < 1.0
        
        print(f"📊 Actual Movement: {actual_movement}")
        
        # Calculate accuracy
        if isinstance(model, AIStockAnalysisModel):
            predicted_movement = prediction_result['prediction']
            prediction_correct = (
                (predicted_movement == "BULLISH" and stock_went_up) or
                (predicted_movement == "BEARISH" and not stock_went_up) or
                (predicted_movement == "NEUTRAL" and abs(price_change_percent) < 1.0)
            )
        else:
            # For rule-based model, check if buy signal was correct
            prediction_correct = (should_buy and stock_went_up) or (not should_buy and not stock_went_up)
        
        # Step 5: Use evaluator for additional metrics
        print("\n5. Using trading bench evaluator...")
        
        evaluator = ReturnEvaluator()
        
        # Calculate return if we followed the prediction
        if should_buy and price_change > 0:
            trade_return = price_change_percent / 100
            trade_outcome = "✅ PROFIT"
        elif should_buy and price_change < 0:
            trade_return = price_change_percent / 100  # Negative
            trade_outcome = "❌ LOSS"
        elif not should_buy and price_change > 0:
            trade_return = 0  # Missed opportunity
            trade_outcome = "😐 MISSED OPPORTUNITY"
        else:
            trade_return = 0  # Correctly avoided loss
            trade_outcome = "✅ CORRECTLY AVOIDED"
        
        print(f"💰 Trade Outcome: {trade_outcome}")
        print(f"💱 Potential Return: {trade_return:.4f} ({trade_return*100:.2f}%)")
        
        # Step 6: Final Results
        print("\n" + "=" * 60)
        print("EVALUATION RESULTS")
        print("=" * 60)
        print(f"Ticker: {ticker}")
        print(f"Yesterday's Price: ${yesterday_price:.2f}")
        print(f"Today's Price: ${today_price:.2f}")
        print(f"Price Change: {price_change_percent:.2f}%")
        print(f"Prediction Correct: {'YES' if prediction_correct else 'NO'}")
        print(f"Trade Outcome: {trade_outcome}")
        
        # Overall result
        if prediction_correct and trade_return > 0:
            result = "🟢 EXCELLENT"
        elif prediction_correct:
            result = "🟡 GOOD"
        else:
            result = "🔴 NEEDS IMPROVEMENT"
            
        print(f"Overall Score: {result}")
        
    except Exception as e:
        print(f"❌ Error in evaluation: {e}")


if __name__ == '__main__':
    # Run original demo
    # main()
    
    # Run AI evaluation demo
    ai_stock_evaluation_demo()

#!/usr/bin/env python3
"""
Test script to verify the new evaluator structure works correctly
"""

import sys
import os
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Test imports from the new evaluator package
from trading_bench.evaluators import (
    BaseEvaluator,
    PositionTracker,
    StockEvaluator,
    PolymarketEvaluator,
    eval_stock,
    eval_polymarket,
    calculate_kelly_criterion,
    analyze_market_efficiency
)


def test_stock_evaluator():
    """Test the stock evaluator functionality"""
    print("🧪 Testing Stock Evaluator")
    print("-" * 40)
    
    # Test with simple stock actions
    actions = [
        {
            "ticker": "AAPL",
            "action": "buy",
            "timestamp": "2024-01-15",
            "price": 150.0,
            "quantity": 10
        },
        {
            "ticker": "AAPL",
            "action": "sell",
            "timestamp": "2024-01-20",
            "price": 155.0,
            "quantity": 5
        }
    ]
    
    # Test legacy eval function
    print("Testing legacy eval function...")
    result = eval_stock(actions)
    print(f"Legacy eval result: ${result:.2f}")
    
    # Test new StockEvaluator class
    print("\nTesting StockEvaluator class...")
    evaluator = StockEvaluator()
    detailed_result = evaluator.evaluate(actions)
    print(f"Detailed eval result: ${detailed_result['total_pnl']:.2f}")
    print(f"Total trades: {detailed_result['total_trades']}")
    print(f"Evaluator type: {detailed_result['evaluator_type']}")
    
    return True


def test_polymarket_evaluator():
    """Test the polymarket evaluator functionality"""
    print("\n🧪 Testing Polymarket Evaluator")
    print("-" * 40)
    
    # Test with simple polymarket actions
    actions = [
        {
            "market_id": "test_market",
            "outcome": "yes",
            "action": "buy",
            "timestamp": "2024-01-15",
            "price": 0.6,
            "quantity": 100
        },
        {
            "market_id": "test_market",
            "outcome": "yes",
            "action": "sell",
            "timestamp": "2024-01-20",
            "price": 0.7,
            "quantity": 50
        }
    ]
    
    market_outcomes = {
        "test_market": {
            "result": "yes",
            "resolution_date": "2024-01-31"
        }
    }
    
    # Test legacy eval function
    print("Testing legacy eval_polymarket function...")
    result = eval_polymarket(actions, market_outcomes)
    print(f"Legacy eval result: ${result['total_pnl']:.2f}")
    
    # Test new PolymarketEvaluator class
    print("\nTesting PolymarketEvaluator class...")
    evaluator = PolymarketEvaluator()
    detailed_result = evaluator.evaluate(actions, market_outcomes)
    print(f"Detailed eval result: ${detailed_result['total_pnl']:.2f}")
    print(f"Total trades: {detailed_result['total_trades']}")
    print(f"Prediction accuracy: {detailed_result['prediction_accuracy']:.1%}")
    print(f"Evaluator type: {detailed_result['evaluator_type']}")
    
    return True


def test_base_evaluator():
    """Test the base evaluator functionality"""
    print("\n🧪 Testing Base Evaluator")
    print("-" * 40)
    
    # Test PositionTracker
    print("Testing PositionTracker...")
    tracker = PositionTracker()
    
    # Add some positions
    tracker.update_position("AAPL", "buy", 150.0, 10)
    tracker.update_position("AAPL", "buy", 155.0, 5)
    tracker.update_position("AAPL", "sell", 160.0, 3)
    
    position = tracker.get_position("AAPL")
    print(f"AAPL position: {position['quantity']} shares @ ${position['avg_price']:.2f}")
    
    # Test unrealized P&L calculation
    current_prices = {"AAPL": 165.0}
    unrealized_pnl = tracker.calculate_unrealized_pnl(current_prices)
    print(f"Unrealized P&L: ${unrealized_pnl:.2f}")
    
    return True


def test_utility_functions():
    """Test utility functions"""
    print("\n🧪 Testing Utility Functions")
    print("-" * 40)
    
    # Test Kelly criterion
    print("Testing Kelly criterion...")
    kelly = calculate_kelly_criterion(0.6, 100, 80)
    print(f"Kelly criterion: {kelly:.4f}")
    
    # Test market efficiency analysis
    print("\nTesting market efficiency analysis...")
    actions = [
        {"market_id": "test", "price": 0.5, "outcome": "yes"},
        {"market_id": "test", "price": 0.6, "outcome": "yes"},
        {"market_id": "test", "price": 0.55, "outcome": "no"},
    ]
    outcomes = {"test": {"result": "yes"}}
    
    efficiency = analyze_market_efficiency(actions, outcomes)
    print(f"Market efficiency results: {efficiency}")
    
    return True


def main():
    """Run all tests"""
    print("🚀 Testing New Evaluator Structure")
    print("=" * 50)
    
    tests = [
        test_stock_evaluator,
        test_polymarket_evaluator,
        test_base_evaluator,
        test_utility_functions
    ]
    
    results = []
    for test in tests:
        try:
            success = test()
            results.append(success)
            print("✅ PASSED")
        except Exception as e:
            print(f"❌ FAILED: {e}")
            results.append(False)
    
    print(f"\n🎯 Test Results: {sum(results)}/{len(results)} tests passed")
    
    if all(results):
        print("🎉 All tests passed! The new evaluator structure is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
    
    return all(results)


if __name__ == "__main__":
    main() 
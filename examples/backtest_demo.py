#!/usr/bin/env python3
"""
Backtesting Demo - Simple and clean

Shows how to run backtests using existing infrastructure.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from live_trade_bench.backtesting import run_backtest


def main() -> None:
    """Run a simple backtest demo."""
    print("📈 Backtesting Demo")
    print("=" * 50)

    # Test with trading days (avoid holidays)
    start_date = "2024-01-02"  # Avoid New Year's Day
    end_date = "2024-01-05"  # Short test period

    print(f"🚀 Running backtest: {start_date} → {end_date}")

    try:
        backtest_agent = {"initial_cash": 1000, "model": "gpt-4o-mini"}
        results = run_backtest(start_date, end_date, {"backtest_agent": backtest_agent})

        print("\n📊 Backtest Results:")
        print(f"   Period: {results['start_date']} → {results['end_date']}")
        print(f"   Trading days: {results['total_days']}")

        print("\n🏆 Agent Performance:")
        for agent_name, perf in results["agents"].items():
            print(f"   {agent_name}:")
            print(f"     Initial: ${perf['initial_value']:,.2f}")
            print(f"     Final: ${perf['final_value']:,.2f}")
            print(f"     Return: {perf['return_percentage']:+.2f}%")

        print("\n📰 Note: Historical news analysis integrated into AI decision making")

    except Exception as e:
        print(f"❌ Backtest failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()

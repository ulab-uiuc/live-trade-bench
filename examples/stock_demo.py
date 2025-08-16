#!/usr/bin/env python3
"""
Stock Trading Demo - Long Running Live Trading System

This demo runs continuously, checking market hours and trading during open periods.
"""

import sys
from pathlib import Path

from live_trade_bench import StockTradingSystem

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def main() -> None:
    """Multi-stock AI trading demo"""
    print("📈 Multi-Stock AI Trading Demo")
    print("=" * 60)

    # Create trading system
    system = StockTradingSystem()

    # Add AI agents with higher initial cash for multiple stocks
    system.add_agent("Portfolio_Alice", 2000.0, "gpt-4o-mini")

    try:
        print("\n🚀 Starting stock trading...")
        system.run(
            duration_minutes=5, interval=30
        )  # Run for 5 minutes with 30s intervals
    except Exception as e:
        print(f"❌ System error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()

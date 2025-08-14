#!/usr/bin/env python3
"""
Stock Trading Demo - Long Running Live Trading System

This demo runs continuously, checking market hours and trading during open periods.
"""

import sys
from pathlib import Path

from trading_bench import StockTradingSystem

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def main():
    """Multi-stock AI trading demo"""
    print("📈 Multi-Stock AI Trading Demo")
    print("=" * 60)

    # Create trading system
    system = StockTradingSystem()

    # Add AI agents with higher initial cash for multiple stocks
    system.add_agent("Portfolio_Alice", 2000.0, "gpt-4o-mini")

    print("\n🎯 Multi-Stock Architecture:")
    print("   • AI agents analyze all 10 stocks each cycle")
    print("   • Portfolio diversification considerations")
    print("   • Risk management across positions")
    print("   • LLM-powered decision making")

    # Run the multi-stock system
    try:
        print("\n🚀 Starting multi-stock AI trading...")
        system.run(cycles=1000, interval=60.0)
    except Exception as e:
        print(f"❌ System error: {e}")
        import traceback

        traceback.print_exc()

    print("\n✅ Multi-Stock AI Trading Demo completed!")
    print("\n💡 Key Features Demonstrated:")
    print("   • Portfolio diversification across sectors")
    print("   • AI-driven stock selection and sizing")
    print("   • Risk management with limited cash")
    print("   • Real-time multi-stock analysis")
    print("\n🔧 To enable full functionality:")
    print("   1. Install: pip install litellm yfinance")
    print("   2. Set: export OPENAI_API_KEY=your_key")
    print("   3. Experiment with different stock combinations")


if __name__ == "__main__":
    main()

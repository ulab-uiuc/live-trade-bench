#!/usr/bin/env python3
"""
Polymarket AI Trading Demo

This demo showcases AI-powered prediction market trading using LLM agents.
Each agent analyzes market conditions and makes trading decisions.
"""

import sys
from pathlib import Path

from live_trade_bench import PolymarketTradingSystem

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def main() -> None:
    """Main prediction market trading demo"""
    print("🎯 Polymarket AI Trading Demo")
    print("=" * 60)

    # Create prediction market trading system
    system = PolymarketTradingSystem()

    # Add AI agents with funds for prediction market trading
    system.add_agent("Predictor_Alice", 400.0, "gpt-4o-mini")

    # Run the prediction market system for a specified duration
    try:
        print("\n🚀 Starting prediction market trading...")
        system.run(
            duration_minutes=5, interval=30
        )  # Run for 5 minutes with 30s intervals
    except Exception as e:
        print(f"❌ System error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()

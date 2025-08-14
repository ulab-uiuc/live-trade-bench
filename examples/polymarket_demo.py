#!/usr/bin/env python3
"""
Polymarket Trading Demo - AI-powered prediction market trading
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from trading_bench import PolymarketTradingSystem


def main():
    """Main prediction market trading demo"""
    print("🎯 Polymarket AI Trading Demo")
    print("=" * 60)

    # Create prediction market trading system
    system = PolymarketTradingSystem()

    # Add AI agents with funds for prediction market trading
    system.add_agent("Predictor_Alice", 400.0, "gpt-4o-mini")

    print("\n🎯 Prediction Market Features:")
    print("   • AI agents analyze market fundamentals")
    print("   • YES/NO outcome predictions")
    print("   • Real market data from Polymarket API")
    print("   • Portfolio diversification across markets")

    print("\n📊 Market Categories:")
    print("   • Crypto: Bitcoin price predictions")
    print("   • Politics: Election outcomes")
    print("   • Technology: AI breakthroughs")
    print("   • Economics: Climate and policy targets")

    # Run the prediction market system
    try:
        print("\n🚀 Starting prediction market trading...")
        system.run(cycles=4, interval=2.0)
    except Exception as e:
        print(f"❌ System error: {e}")
        import traceback

        traceback.print_exc()

    print("\n✅ Polymarket Trading Demo completed!")
    print("\n💡 Key Features Demonstrated:")
    print("   • LLM-powered market analysis")
    print("   • Automated prediction market trading")
    print("   • Risk assessment and position sizing")
    print("   • Multi-market portfolio management")
    print("   • Category-specific analysis context")
    print("\n🔧 To enable full functionality:")
    print("   1. Install: pip install litellm")
    print("   2. Set: export OPENAI_API_KEY=your_key")
    print("   3. Explore different prediction categories")
    print("\n🏗️ Architecture:")
    print("   • AIPolymarketAgent: trading_bench/agents/polymarket_agent.py")
    print("   • PolymarketAccount: trading_bench/evaluators/polymarket_account.py")
    print("   • Data Source: trading_bench/fetchers/polymarket_fetcher.py")


if __name__ == "__main__":
    main()

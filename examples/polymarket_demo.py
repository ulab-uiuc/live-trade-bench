#!/usr/bin/env python3
"""
Polymarket Trading Demo - AI-powered prediction market trading
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from trading_bench import AIPolymarketAgent, PolymarketTradingSystem


def main():
    """Main prediction market trading demo"""
    print("🎯 Polymarket AI Trading Demo")
    print("=" * 60)

    # Create prediction market trading system
    system = PolymarketTradingSystem()

    # Add AI agents with funds for prediction market trading
    system.add_agent("Predictor_Alice", 400.0, "gpt-4o-mini")

    print(f"\n🎯 Prediction Market Features:")
    print(f"   • AI agents analyze market fundamentals")
    print(f"   • YES/NO outcome predictions")
    print(f"   • Real market data from Polymarket API")
    print(f"   • Portfolio diversification across markets")

    print(f"\n📊 Market Categories:")
    print(f"   • Crypto: Bitcoin price predictions")
    print(f"   • Politics: Election outcomes")
    print(f"   • Technology: AI breakthroughs")
    print(f"   • Economics: Climate and policy targets")

    # Run the prediction market system
    try:
        print(f"\n🚀 Starting prediction market trading...")
        system.run(cycles=4, interval=2.0)
    except Exception as e:
        print(f"❌ System error: {e}")
        import traceback
        traceback.print_exc()

    print(f"\n✅ Polymarket Trading Demo completed!")
    print(f"\n💡 Key Features Demonstrated:")
    print(f"   • LLM-powered market analysis")
    print(f"   • Automated prediction market trading")
    print(f"   • Risk assessment and position sizing")
    print(f"   • Multi-market portfolio management")
    print(f"   • Category-specific analysis context")
    print(f"\n🔧 To enable full functionality:")
    print(f"   1. Install: pip install litellm")
    print(f"   2. Set: export OPENAI_API_KEY=your_key")
    print(f"   3. Explore different prediction categories")
    print(f"\n🏗️ Architecture:")
    print(f"   • AIPolymarketAgent: trading_bench/agents/polymarket_agent.py")
    print(f"   • PolymarketAccount: trading_bench/evaluators/polymarket_account.py")
    print(f"   • Data Source: trading_bench/fetchers/polymarket_fetcher.py")


if __name__ == "__main__":
    main()

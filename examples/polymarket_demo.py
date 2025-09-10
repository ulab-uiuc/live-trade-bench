#!/usr/bin/env python3
"""
Polymarket Portfolio Management Demo - Modern Portfolio Allocation System

This demo showcases the new portfolio management approach using AI agents
to generate allocation targets and automatically rebalance portfolios for prediction markets.
"""

from live_trade_bench.systems.polymarket_system import PolymarketPortfolioSystem


def main() -> None:
    """Polymarket portfolio management demo with AI agents"""
    print("📊 Polymarket Portfolio Management Demo")
    print("=" * 60)

    # Create portfolio management system
    system = PolymarketPortfolioSystem()

    # Add AI agents for portfolio management
    system.add_agent(
        "Portfolio_Manager", 2000.0, "anthropic/claude-3-5-sonnet-20240620"
    )

    print(f"✅ Created system with {len(system.universe)} markets")
    print(f"✅ Added agents: {list(system.agents.keys())}")

    try:
        print("\n🚀 Starting polymarket portfolio management...")
        for i in range(4):
            system.run_cycle()

        print("\n📊 Demo finished.")

    except KeyboardInterrupt:
        print("\n⏹️ Demo stopped by user")
    except Exception as e:
        print(f"❌ System error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()

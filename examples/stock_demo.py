#!/usr/bin/env python3
"""
Stock Portfolio Management Demo - Modern Portfolio Allocation System

This demo showcases the new portfolio management approach using AI agents
to generate allocation targets and automatically rebalance portfolios.
"""

from live_trade_bench.systems.stock_system import StockPortfolioSystem


def main() -> None:
    """Stock portfolio management demo with AI agents"""
    print("📊 Stock Portfolio Management Demo")
    print("=" * 60)

    # Create portfolio management system
    system = StockPortfolioSystem()

    # Add AI agents for portfolio management
    system.add_agent("Portfolio_Manager", 10000.0, "gpt-4o-mini")

    # Initialize system and fetch trending stocks
    print("\n🔄 Initializing system and fetching trending stocks...")
    system.initialize_for_live()

    print(
        f"✅ Created system with {len(system.universe)} stocks: {system.universe[:5]}..."
    )
    print(f"✅ Added agents: {list(system.agents.keys())}")

    try:
        print("\n🚀 Starting stock portfolio management...")
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

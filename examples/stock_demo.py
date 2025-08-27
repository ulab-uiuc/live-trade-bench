#!/usr/bin/env python3
"""
Stock Portfolio Management Demo - Modern Portfolio Allocation System

This demo showcases the new portfolio management approach using AI agents
to generate allocation targets and automatically rebalance portfolios.
"""

from live_trade_bench.agents.stock_system import StockPortfolioSystem


def main() -> None:
    """Stock portfolio management demo with AI agents"""
    print("📊 Stock Portfolio Management Demo")
    print("=" * 60)

    # Create portfolio management system
    system = StockPortfolioSystem()

    # Add AI agents for portfolio management
    system.add_agent("Portfolio_Manager", 10000.0, "gpt-4o-mini")

    print(f"✅ Created system with {len(system.universe)} stocks")
    print(f"✅ Added agents: {list(system.agents.keys())}")

    try:
        print("\n🚀 Starting stock portfolio management...")
        print("This will run for 2 minutes with 30-second cycles")
        print("Agents will generate allocation targets and rebalance portfolios")

        # Run the system
        system.run_continuous(interval_minutes=0.5, max_cycles=4)

        print("\n📊 Final Portfolio Summary:")
        summaries = system.get_portfolio_summaries()
        for agent_name, summary in summaries.items():
            print(f"\n🤖 {agent_name}:")
            print(f"   Total Value: ${summary['total_value']:.2f}")
            print(f"   Cash Balance: ${summary['cash_balance']:.2f}")
            print(f"   Target Allocations: {summary['target_allocations']}")
            print(f"   Needs Rebalancing: {summary['needs_rebalancing']}")

    except KeyboardInterrupt:
        print("\n⏹️ Demo stopped by user")
    except Exception as e:
        print(f"❌ System error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()

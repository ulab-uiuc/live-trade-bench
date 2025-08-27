#!/usr/bin/env python3
"""
Polymarket Portfolio Management Demo - Modern Portfolio Allocation System

This demo showcases the new portfolio management approach using AI agents
to generate allocation targets and automatically rebalance portfolios for prediction markets.
"""

from live_trade_bench.agents.polymarket_system import PolymarketPortfolioSystem


def main() -> None:
    """Polymarket portfolio management demo with AI agents"""
    print("📊 Polymarket Portfolio Management Demo")
    print("=" * 60)

    # Create portfolio management system
    system = PolymarketPortfolioSystem()

    # Add AI agents for portfolio management
    system.add_agent("Portfolio_Manager", 2000.0, "gpt-4o-mini")

    print(f"✅ Created system with {len(system.universe)} markets")
    print(f"✅ Added agents: {list(system.agents.keys())}")

    try:
        print("\n🚀 Starting polymarket portfolio management...")
        print("This will run for 2 minutes with 30-second cycles")
        print("Agents will generate allocation targets and rebalance portfolios")

        # Run the system
        system.run_continuous(interval_minutes=0.5, max_cycles=4)

        print("\n📊 Final Portfolio Summary:")
        summaries = system.get_portfolio_summaries()

        # Display individual agent summaries
        for agent_name, summary in summaries.items():
            if agent_name != "OVERALL":
                print(f"\n🤖 {agent_name}:")
                print(f"   💰 Total Value: ${summary['total_value']:,.2f}")
                print(
                    f"   💵 Cash: ${summary['cash_value']:,.2f} ({summary['cash_allocation']:.1%})"
                )
                print(
                    f"   📈 Positions: ${summary['positions_value']:,.2f} ({summary['positions_allocation']:.1%})"
                )
                print(f"   🎯 Target Allocations: {summary['target_allocations']}")
                print(f"   📊 Current Allocations: {summary['current_allocations']}")
                print(f"   🔄 Needs Rebalancing: {summary['needs_rebalancing']}")

        # Display overall portfolio summary
        if "OVERALL" in summaries:
            overall = summaries["OVERALL"]
            print("\n🏆 OVERALL PORTFOLIO:")
            print(f"   💰 Total Portfolio Value: ${overall['total_value']:,.2f}")
            print(
                f"   💵 Total Cash: ${overall['cash_value']:,.2f} ({overall['cash_allocation']:.1%})"
            )
            print(
                f"   📈 Total Positions: ${overall['positions_value']:,.2f} ({overall['positions_allocation']:.1%})"
            )
            print(f"   🔄 Overall Rebalancing Needed: {overall['needs_rebalancing']}")

    except KeyboardInterrupt:
        print("\n⏹️ Demo stopped by user")
    except Exception as e:
        print(f"❌ System error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()

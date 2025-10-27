"""
BitMEX Portfolio System Demo

Demonstrates how to use the BitMEX trading system with LLM agents.
"""

import sys
from pathlib import Path

from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
load_dotenv()

from live_trade_bench.systems import BitMEXPortfolioSystem


def main():
    """Run a simple BitMEX trading demo."""
    print("=" * 60)
    print("BitMEX Portfolio System Demo")
    print("=" * 60)

    # Create system instance
    print("\n1. Creating BitMEX Portfolio System...")
    system = BitMEXPortfolioSystem(universe_size=12)

    # Initialize for live trading (fetches trending contracts)
    print("\n2. Initializing for live trading...")
    system.initialize_for_live()
    print(f"   Universe: {system.universe}")

    # Add demo agents
    print("\n3. Adding demo agents...")
    agents = [
        ("GPT-4o Demo", "openai/gpt-4o", 10000.0),
        ("Claude-Sonnet-4 Demo", "anthropic/claude-sonnet-4-20250514", 10000.0),
    ]

    for name, model, cash in agents:
        system.add_agent(name, cash, model)
        print(f"   Added: {name} (${cash:,.0f})")

    # Run one trading cycle
    print("\n4. Running trading cycle...")
    try:
        system.run_cycle()
    except Exception as e:
        print(f"   Error during cycle: {e}")
        print("   (This is expected if LLM API keys are not configured)")

    # Display results
    print("\n5. Agent Performance Summary:")
    print("-" * 60)
    for agent_name, account in system.accounts.items():
        total_value = account.get_total_value()
        profit = total_value - account.initial_cash
        performance = (profit / account.initial_cash) * 100

        print(f"\n{agent_name}:")
        print(f"  Total Value: ${total_value:,.2f}")
        print(f"  Profit/Loss: ${profit:,.2f} ({performance:+.2f}%)")
        print(f"  Cash Balance: ${account.cash_balance:,.2f}")

        positions = account.get_positions()
        if positions:
            print(f"  Positions ({len(positions)}):")
            for symbol, position in list(positions.items())[:5]:
                value = position.market_value
                pnl = position.unrealized_pnl
                print(f"    {symbol}: {position.quantity:.4f} contracts "
                      f"(value: ${value:,.2f}, PnL: ${pnl:+,.2f})")
        else:
            print("  Positions: None (100% cash)")

    print("\n" + "=" * 60)
    print("Demo completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()

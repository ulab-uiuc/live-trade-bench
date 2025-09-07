"""
Multi-Model Backtest Demo - AI Trading Competition

Quick backtest demo with a few models for testing.
For production-grade demo, see enhanced_backtest_demo.py

Tests multiple AI models concurrently in historical trading scenarios.
Requires: TOGETHER_API_KEY and OPENAI_API_KEY environment variables.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from live_trade_bench.backtesting import run_backtest


async def main():
    """Backtest demo main function."""
    print("🔮 Multi-Model Portfolio Backtest Demo")
    print("Testing 4 different AI models concurrently")
    print()
    print("💡 For production-grade demo with all models, run:")
    print("   python enhanced_backtest_demo.py")
    print()

    # Test with trading days (avoid holidays)
    start_date = "2024-01-02"  # Avoid New Year's Day
    end_date = "2024-01-03"  # Short test period

    print(f"🚀 Running backtest: {start_date} → {end_date}")

    try:
        # Define multiple agents with different models from async_demo
        agents_config = {
            "Qwen_Agent": {
                "initial_cash": 1000,
                "model": "together:Qwen/Qwen2.5-7B-Instruct-Turbo",
            },
            "Llama_Agent": {
                "initial_cash": 1000,
                "model": "together:meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
            },
            "GPT5_Agent": {"initial_cash": 1000, "model": "openai:gpt-5"},
            "GPT4o_Mini_Agent": {"initial_cash": 1000, "model": "openai:gpt-4o-mini"},
        }

        print(f"🤖 Testing {len(agents_config)} AI models:")
        for agent_name, config in agents_config.items():
            print(f"   • {agent_name}: {config['model']}")

        results = await run_backtest(start_date, end_date, agents_config)

        print("\n📊 Backtest Results:")
        print(f"   Period: {results['start_date']} → {results['end_date']}")
        print(f"   Trading days: {results['total_days']}")

        print("\n🏆 AI Model Performance Comparison:")
        print("=" * 60)

        # Sort agents by return percentage for ranking
        sorted_agents = sorted(
            results["agents"].items(),
            key=lambda x: x[1]["return_percentage"],
            reverse=True,
        )

        for rank, (agent_name, perf) in enumerate(sorted_agents, 1):
            model_name = (
                agents_config[agent_name]["model"].split(":")[-1].split("/")[-1]
            )
            print(f"   #{rank} {agent_name} ({model_name}):")
            print(f"        Initial: ${perf['initial_value']:,.2f}")
            print(f"        Final:   ${perf['final_value']:,.2f}")
            print(f"        Return:  {perf['return_percentage']:+.2f}%")
            print()

        # Find the best performing model
        best_agent, best_perf = sorted_agents[0]
        best_model = agents_config[best_agent]["model"]
        print(f"🏅 Best Performer: {best_agent}")
        print(f"   Model: {best_model}")
        print(f"   Return: {best_perf['return_percentage']:+.2f}%")

        print("\n📰 Note: All models used same historical data and news analysis")
        print("💡 Tip: Set TOGETHER_API_KEY and OPENAI_API_KEY for all models to work")

    except Exception as e:
        print(f"❌ Backtest failed: {e}")
        import traceback

        traceback.print_exc()

    finally:
        # 🧹 CRITICAL: Force cleanup of litellm's lingering async resources
        # This prevents the program from hanging after completion
        print("🧹 Cleaning up async resources...")

        try:
            # Cancel all remaining background tasks created by litellm
            pending_tasks = [
                task
                for task in asyncio.all_tasks()
                if not task.done() and task != asyncio.current_task()
            ]

            if pending_tasks:
                print(f"   🔍 Found {len(pending_tasks)} background tasks to cleanup")

                # Cancel all pending tasks
                for task in pending_tasks:
                    task.cancel()

                # Wait briefly for cancellation with timeout to avoid infinite recursion
                try:
                    await asyncio.wait_for(
                        asyncio.gather(*pending_tasks, return_exceptions=True),
                        timeout=2.0,
                    )
                    print("   ✅ Background tasks cleaned up successfully")
                except asyncio.TimeoutError:
                    print("   ⚠️ Cleanup timeout - forcing exit")
                except Exception as cleanup_error:
                    print(f"   ⚠️ Cleanup error (ignoring): {cleanup_error}")
            else:
                print("   ✅ No background tasks to cleanup")

        except Exception as e:
            print(f"   ⚠️ Cleanup failed (ignoring): {e}")

        print("🎯 Backtest completed - program should exit cleanly now")


if __name__ == "__main__":
    asyncio.run(main())

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

    start_date = "2024-01-02"  # Avoid New Year's Day
    end_date = "2024-01-06"  # Short test period

    print(f"🚀 Running backtest: {start_date} → {end_date}")

    try:
        models = [
            #("Qwen_Agent", "together:Qwen/Qwen2.5-7B-Instruct-Turbo"),
            #("Llama_Agent", "together:meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"),
            ("GPT5_Agent", "openai:gpt-5"),
            #("GPT4o_Mini_Agent", "openai:gpt-4o-mini"),
        ]

        print(f"🤖 Testing {len(models)} AI models:")
        for name, model_id in models:
            print(f"   • {name}: {model_id}")

        # run_backtest 是同步函数
        results = run_backtest(
            models=models,
            initial_cash=1000.0,
            start_date=start_date,
            end_date=end_date,
            market_type="stock",
        )

        print("\n📊 Backtest Results (per agent):")
        print("=" * 60)

        # results 已是每个 agent 的摘要字典
        # {agent_name: {initial_value, final_value, return_percentage, period}}
        sorted_agents = sorted(
            results.items(),
            key=lambda x: x[1]["return_percentage"],
            reverse=True,
        )

        for rank, (agent_name, perf) in enumerate(sorted_agents, 1):
            model_name = next((m for n, m in models if n == agent_name), "?")
            print(f"   #{rank} {agent_name} ({model_name}):")
            print(f"        Initial: ${perf['initial_value']:,.2f}")
            print(f"        Final:   ${perf['final_value']:,.2f}")
            print(f"        Return:  {perf['return_percentage']:+.2f}%")
            print()

        best_agent, best_perf = sorted_agents[0]
        best_model = next((m for n, m in models if n == best_agent), "?")
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

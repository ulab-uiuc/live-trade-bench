"""
Multi-Model Parallel Backtest Demo - AI Trading Competition

Quick parallel backtest demo with multiple models for testing.
Uses parallel processing for both stock and polymarket backtests.
For production-grade demo, see enhanced_backtest_demo.py

Tests multiple AI models concurrently in historical trading scenarios.
Requires: TOGETHER_API_KEY and OPENAI_API_KEY environment variables.
"""

import asyncio
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.app.config import get_base_model_configs
from live_trade_bench.backtesting import run_backtest


async def main():
    """Parallel backtest demo main function."""
    print("🔮 Multi-Model Parallel Portfolio Backtest Demo")
    print("Testing AI models concurrently across Stock & Polymarket")
    print("=" * 60)
    print("💡 For production-grade demo with all models, run:")
    print("   python enhanced_backtest_demo.py")
    print()

    start_date = "2025-01-02"  # Avoid New Year's Day
    end_date = "2025-01-04"  # Short test period

    print(f"🚀 Running parallel backtest: {start_date} → {end_date}")
    print(f"⏰ Started at: {datetime.now().strftime('%H:%M:%S')}")

    try:
        # Use centralized model configurations
        models = get_base_model_configs()

        print(f"🤖 Testing {len(models)} AI models on both markets:")
        for name, model_id in models:
            print(f"   • {name}: {model_id}")

        # 分别运行股票和预测市场回测
        print("📈 Running stock market backtest...")
        stock_results = run_backtest(
            models=models,
            initial_cash=1000.0,
            start_date=start_date,
            end_date=end_date,
            market_type="stock",
        )

        print("🎯 Running polymarket backtest...")
        polymarket_results = run_backtest(
            models=models,
            initial_cash=500.0,
            start_date=start_date,
            end_date=end_date,
            market_type="polymarket",
        )

        results = {
            "stock": stock_results,
            "polymarket": polymarket_results,
        }

        print(
            f"\n✅ Parallel backtest completed at: {datetime.now().strftime('%H:%M:%S')}"
        )
        print("\n📊 Backtest Results Summary:")
        print("=" * 80)

        # 显示股票市场结果
        stock_results = results.get("stock", {})
        if stock_results:
            print("\n� STOCK MARKET RESULTS:")
            print("-" * 40)
            sorted_stock = sorted(
                stock_results.items(),
                key=lambda x: x[1].get("return_percentage", 0),
                reverse=True,
            )

            for rank, (agent_name, perf) in enumerate(sorted_stock, 1):
                model_name = next((m for n, m in models if n == agent_name), "?")
                print(f"   #{rank} {agent_name} ({model_name}):")
                print(f"        Initial: ${perf.get('initial_value', 0):,.2f}")
                print(f"        Final:   ${perf.get('final_value', 0):,.2f}")
                print(f"        Return:  {perf.get('return_percentage', 0):+.2f}%")
                print()

        # 显示预测市场结果
        polymarket_results = results.get("polymarket", {})
        if polymarket_results:
            print("\n🎯 POLYMARKET RESULTS:")
            print("-" * 40)
            sorted_poly = sorted(
                polymarket_results.items(),
                key=lambda x: x[1].get("return_percentage", 0),
                reverse=True,
            )

            for rank, (agent_name, perf) in enumerate(sorted_poly, 1):
                model_name = next((m for n, m in models if n == agent_name), "?")
                print(f"   #{rank} {agent_name} ({model_name}):")
                print(f"        Initial: ${perf.get('initial_value', 0):,.2f}")
                print(f"        Final:   ${perf.get('final_value', 0):,.2f}")
                print(f"        Return:  {perf.get('return_percentage', 0):+.2f}%")
                print()

        # 总体最佳表现者
        all_results = []
        for market, market_results in [
            ("Stock", stock_results),
            ("Polymarket", polymarket_results),
        ]:
            for agent_name, perf in market_results.items():
                all_results.append((agent_name, perf, market))

        if all_results:
            best_agent, best_perf, best_market = max(
                all_results, key=lambda x: x[1].get("return_percentage", 0)
            )
            best_model = next((m for n, m in models if n == best_agent), "?")

            print("\n🏅 OVERALL BEST PERFORMER:")
            print("-" * 40)
            print(f"   Agent: {best_agent}")
            print(f"   Model: {best_model}")
            print(f"   Market: {best_market}")
            print(f"   Return: {best_perf.get('return_percentage', 0):+.2f}%")

        # 性能统计
        total_models = len(stock_results) + len(polymarket_results)
        print("\n📊 PERFORMANCE STATS:")
        print("-" * 40)
        print(f"   Total Models Tested: {total_models}")
        print(f"   Stock Models: {len(stock_results)}")
        print(f"   Polymarket Models: {len(polymarket_results)}")
        print("   Parallel Processing: ✅ Enabled")
        print(f"   Test Period: {start_date} → {end_date}")

        print("\n📰 Note: All models used same historical data and news analysis")
        print("💡 Tip: Set TOGETHER_API_KEY and OPENAI_API_KEY for all models to work")
        print("🚀 Parallel processing significantly reduces total execution time!")

    except Exception as e:
        print(f"❌ Parallel backtest failed: {e}")
        import traceback

        traceback.print_exc()

    finally:
        print("🎯 Parallel backtest completed - program should exit cleanly now")


if __name__ == "__main__":
    asyncio.run(main())

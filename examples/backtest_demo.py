import asyncio
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.app.config import get_base_model_configs
from backend.app.models_data import _create_model_data, _serialize_positions

# from live_trade_bench.backtest import run_backtest  # Not needed in new architecture


def get_trading_days(start_date: str, end_date: str, interval_days: int = 1) -> List[datetime]:
    """Generate list of trading days with specified interval.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format 
        interval_days: Days between each trading cycle (default: 1 = daily)
    """
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    days = []
    current = start
    
    while current <= end:
        if current.weekday() < 5:  # Monday = 0, Friday = 4 (weekdays only)
            days.append(current)
        current += timedelta(days=1)
    
    # If interval > 1, select dates at specified intervals
    if interval_days > 1:
        selected_days = []
        for i in range(0, len(days), interval_days):
            selected_days.append(days[i])
        return selected_days
    
    return days


def initialize_systems(
    models: List[Tuple[str, str]], trading_days: List[datetime]
) -> Dict[str, Any]:
    """Initialize trading systems for all models and both markets."""
    from live_trade_bench.fetchers.polymarket_fetcher import (
        fetch_verified_historical_markets,
    )
    from live_trade_bench.systems.polymarket_system import PolymarketPortfolioSystem
    from live_trade_bench.systems.stock_system import StockPortfolioSystem

    systems = {"polymarket": {}, "stock": {}}

    print("🏗️ Initializing systems for all models...")

    # ✅ Fetch verified markets ONCE for all Polymarket systems
    print("📊 Fetching verified Polymarket markets (once for all models)...")
    verified_markets = fetch_verified_historical_markets(trading_days, 5)
    print(
        f"   ✅ Found {len(verified_markets)} verified markets to share across all models"
    )

    # Initialize Polymarket systems with shared universe
    for model_name, model_id in models:
        system = PolymarketPortfolioSystem()
        system.add_agent(name=model_name, initial_cash=500.0, model_name=model_id)
        # Use shared verified markets instead of individual initialization
        system.set_universe(verified_markets)
        systems["polymarket"][model_name] = system
        print(f"   ✅ {model_name} Polymarket system ready (shared universe)")

    # Initialize Stock systems
    for model_name, model_id in models:
        system = StockPortfolioSystem()
        system.add_agent(name=model_name, initial_cash=1000.0, model_name=model_id)
        # Initialize for live (stocks don't need special backtest init)
        system.initialize_for_live()
        systems["stock"][model_name] = system
        print(f"   ✅ {model_name} Stock system ready")

    print(
        f"✅ All systems initialized: {len(models)} models × 2 markets = {len(models)*2} systems"
    )
    print(
        f"🚀 Initialization efficiency: 1 market verification → {len(models)} Polymarket systems"
    )
    return systems


def fetch_shared_market_data(date_str: str, systems: Dict) -> Dict[str, Any]:
    """Fetch market data once and share across all models."""
    shared_data = {}

    # Get one representative system for each market type to fetch data
    poly_system = next(iter(systems["polymarket"].values()))
    stock_system = next(iter(systems["stock"].values()))

    print(f"  📊 Fetching shared market data for {date_str}...")

    # Fetch Polymarket data once
    try:
        poly_market_data = poly_system._fetch_market_data(date_str)
        shared_data["polymarket"] = poly_market_data
        print(f"    ✅ Polymarket: {len(poly_market_data)} markets")
    except Exception as e:
        print(f"    ❌ Polymarket fetch failed: {e}")
        shared_data["polymarket"] = {}

    # Fetch Stock data once
    try:
        stock_market_data = stock_system._fetch_market_data(date_str)
        shared_data["stock"] = stock_market_data
        print(f"    ✅ Stock: {len(stock_market_data)} stocks")
    except Exception as e:
        print(f"    ❌ Stock fetch failed: {e}")
        shared_data["stock"] = {}

    return shared_data


def fetch_shared_news_data(
    date_str: str, market_data: Dict, systems: Dict
) -> Dict[str, Any]:
    """Fetch news data once and share across all models."""
    shared_news = {}

    # Get representative systems
    poly_system = next(iter(systems["polymarket"].values()))
    stock_system = next(iter(systems["stock"].values()))

    print(f"  📰 Fetching shared news data for {date_str}...")

    # Fetch Polymarket news once
    try:
        poly_news = poly_system._fetch_news_data(
            market_data.get("polymarket", {}), date_str
        )
        shared_news["polymarket"] = poly_news
        print(f"    ✅ Polymarket news: {len(poly_news)} sources")
    except Exception as e:
        print(f"    ❌ Polymarket news failed: {e}")
        shared_news["polymarket"] = {}

    # Fetch Stock news once
    try:
        stock_news = stock_system._fetch_news_data(
            market_data.get("stock", {}), date_str
        )
        shared_news["stock"] = stock_news
        print(f"    ✅ Stock news: {len(stock_news)} sources")
    except Exception as e:
        print(f"    ❌ Stock news failed: {e}")
        shared_news["stock"] = {}

    return shared_news


def run_single_day_single_model_with_shared_data(
    model_name: str,
    market_type: str,
    date_str: str,
    systems: Dict,
    shared_market_data: Dict,
    shared_news_data: Dict,
) -> Dict:
    """Run a single trading cycle for one model using pre-fetched shared data."""
    try:
        system = systems[market_type][model_name]

        # Use the shared data instead of fetching again
        market_data = shared_market_data.get(market_type, {})
        news_data = shared_news_data.get(market_type, {})

        if not market_data:
            return {
                "model_name": model_name,
                "market_type": market_type,
                "date": date_str,
                "status": "failed",
                "error": "No market data available",
            }

        # Skip data fetching, directly generate allocations and update accounts
        allocations = system._generate_allocations(market_data, news_data, date_str)
        system._update_accounts(allocations, market_data)
        system.cycle_count += 1

        return {
            "model_name": model_name,
            "market_type": market_type,
            "date": date_str,
            "status": "completed",
        }
    except Exception as e:
        print(f"❌ {model_name} ({market_type}) failed on {date_str}: {e}")
        return {
            "model_name": model_name,
            "market_type": market_type,
            "date": date_str,
            "status": "failed",
            "error": str(e),
        }


def get_backtest_config():
    """回测配置 - 可以在这里调整参数"""
    return {
        "start_date": "2025-07-01",   # 开始日期
        "end_date": "2025-09-12",     # 结束日期 (3个月)
        "interval_days": 5,           # 每隔5个交易日运行一次 (~每周)
        "max_workers": 4              # 并发数量
    }

async def main():
    print("🔮 Extended Model-Level Parallel Portfolio Backtest Demo")
    print("Testing 20 AI models × 2 markets = 40 concurrent backtests")
    print("=" * 60)
    print()

    # 获取回测配置
    config = get_backtest_config()
    start_date = config["start_date"]
    end_date = config["end_date"] 
    interval_days = config["interval_days"]

    print(f"🚀 Running extended parallel backtest: {start_date} → {end_date}")
    print(f"📅 Trading cycle interval: Every {interval_days} trading days")
    print(f"⏰ Started at: {datetime.now().strftime('%H:%M:%S')}")

    try:
        # Use centralized model configurations
        models = get_base_model_configs()

        print(f"🤖 Testing {len(models)} AI models on both markets:")
        for name, model_id in models:
            print(f"   • {name}: {model_id}")

        # Get trading days with specified interval
        trading_days = get_trading_days(start_date, end_date, interval_days)
        print(f"📅 Trading period: {len(trading_days)} days ({start_date} → {end_date})")

        # Initialize all systems once
        systems = initialize_systems(models, trading_days)

        # Execute day-by-day with model parallelism within each day
        print("\n🚀 Starting day-by-day parallel execution...")
        max_workers = 4  # Reduced to avoid API rate limits

        for day_idx, trading_day in enumerate(trading_days):
            date_str = trading_day.strftime("%Y-%m-%d")
            print(f"\n===== 📆 Day {day_idx + 1}/{len(trading_days)}: {date_str} =====")

            # Fetch shared data once per day
            shared_market_data = fetch_shared_market_data(date_str, systems)
            shared_news_data = fetch_shared_news_data(
                date_str, shared_market_data, systems
            )

            # Generate tasks for this day: all models × both markets
            day_tasks = []
            for model_name, model_id in models:
                day_tasks.append(
                    (
                        model_name,
                        "polymarket",
                        date_str,
                        systems,
                        shared_market_data,
                        shared_news_data,
                    )
                )
                day_tasks.append(
                    (
                        model_name,
                        "stock",
                        date_str,
                        systems,
                        shared_market_data,
                        shared_news_data,
                    )
                )

            print(
                f"⚡ Running {len(day_tasks)} parallel tasks using shared data for {date_str}"
            )

            # Execute all models in parallel for this day using shared data
            completed_day_tasks = []
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_task = {
                    executor.submit(
                        run_single_day_single_model_with_shared_data, *task
                    ): task
                    for task in day_tasks
                }

                for future in as_completed(future_to_task):
                    task = future_to_task[future]
                    try:
                        result = future.result()
                        completed_day_tasks.append(result)
                        if result["status"] == "completed":
                            model_name, market_type = task[:2]
                            print(f"   ✅ {model_name} ({market_type})")
                    except Exception as e:
                        model_name, market_type = task[:2]
                        print(f"   ❌ {model_name} ({market_type}): {e}")

            success_count = sum(
                1 for task in completed_day_tasks if task["status"] == "completed"
            )
            print(
                f"📊 Day {day_idx + 1} summary: {success_count}/{len(day_tasks)} tasks successful"
            )
            print(f"🚀 Data efficiency: 2 API calls → {len(day_tasks)} model executions")

        # Collect final results from all systems
        print("\n📋 Collecting final results from all systems...")
        polymarket_results = {}
        stock_results = {}

        # Collect results from Polymarket systems
        for model_name, system in systems["polymarket"].items():
            for agent_name, account in system.accounts.items():
                initial_cash = account.initial_cash
                final_value = account.get_total_value()
                return_pct = (
                    ((final_value - initial_cash) / initial_cash) * 100
                    if initial_cash > 0
                    else 0
                )

                polymarket_results[agent_name] = {
                    "initial_value": initial_cash,
                    "final_value": final_value,
                    "return_percentage": return_pct,
                    "period": f"{start_date} to {end_date}",
                }

        # Collect results from Stock systems
        for model_name, system in systems["stock"].items():
            for agent_name, account in system.accounts.items():
                initial_cash = account.initial_cash
                final_value = account.get_total_value()
                return_pct = (
                    ((final_value - initial_cash) / initial_cash) * 100
                    if initial_cash > 0
                    else 0
                )

                stock_results[agent_name] = {
                    "initial_value": initial_cash,
                    "final_value": final_value,
                    "return_percentage": return_pct,
                    "period": f"{start_date} to {end_date}",
                }

        results = {
            "stock": stock_results,
            "polymarket": polymarket_results,
        }

        print(
            f"\n✅ Parallel backtest completed at: {datetime.now().strftime('%H:%M:%S')}"
        )
        print("\n📊 Backtest Results Summary:")
        print("=" * 80)

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
        print(
            "🚀 Day-by-day + Model-level parallel processing with shared data caching!"
        )
        print(
            f"⚡ Executed {len(trading_days)} days × {len(models)*2} models using max {max_workers} worker threads"
        )
        print(
            f"📊 Data efficiency: {len(trading_days)*2} API calls (vs {len(trading_days)*len(models)*2} without caching)"
        )

        # Save detailed results to JSON file using the same format as live trading
        print("\n💾 Saving detailed backtest data to backend/models_data_init.json...")
        all_models_data = []

        # Process all systems data from the maintained systems dict
        for market_type, market_systems in systems.items():
            for model_name, system in market_systems.items():
                if hasattr(system, "accounts") and hasattr(system, "agents"):
                    for agent_name, account in system.accounts.items():
                        if agent_name in system.agents:
                            agent = system.agents[agent_name]
                            model_data = _create_model_data(agent, account, market_type)
                            all_models_data.append(_serialize_positions(model_data))

        # Save in the same array format as live trading data
        with open("backend/models_data_init.json", "w") as f:
            json.dump(all_models_data, f, indent=4)

        print(
            f"✅ Backtest data saved successfully! Generated {len(all_models_data)} model entries."
        )

    except Exception as e:
        print(f"❌ Parallel backtest failed: {e}")
        import traceback

        traceback.print_exc()

    finally:
        print("🎯 Parallel backtest completed - program should exit cleanly now")


if __name__ == "__main__":
    asyncio.run(main())

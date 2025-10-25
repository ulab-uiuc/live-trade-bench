import json
import os
from dataclasses import asdict
from datetime import datetime, timedelta

from live_trade_bench.accounts.base_account import Position

from .config import MODELS_DATA_FILE, MODELS_DATA_HIST_FILE, MODELS_DATA_INIT_FILE


def _filter_recent_days(allocation_history, days=30):
    """Filter allocation history to keep only recent N days."""
    if not allocation_history:
        return []

    # Find the most recent timestamp
    dates = []
    for snapshot in allocation_history:
        if ts := snapshot.get("timestamp"):
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                dates.append((dt, snapshot))
            except ValueError:
                pass

    if not dates:
        return allocation_history

    dates.sort(key=lambda x: x[0])
    most_recent = dates[-1][0]
    cutoff = most_recent - timedelta(days=days)

    # Filter snapshots within the date range
    return [snapshot for dt, snapshot in dates if dt >= cutoff]


def _strip_llm_data_except_last(allocation_history):
    """Remove llm_input and llm_output from all snapshots except the last one."""
    if not allocation_history:
        return []

    result = []
    for i, snapshot in enumerate(allocation_history):
        snapshot_copy = snapshot.copy()
        # Keep LLM data only in the last snapshot
        if i < len(allocation_history) - 1:
            snapshot_copy.pop("llm_input", None)
            snapshot_copy.pop("llm_output", None)
        result.append(snapshot_copy)

    return result


def _create_compact_model_data(model_data):
    """Create a compact version of model data for frontend (30 days + last LLM only)."""
    compact = model_data.copy()

    # Filter to recent 30 days
    allocation_history = compact.get("allocationHistory", [])
    original_trades_count = len(allocation_history)  # Preserve original count
    recent_history = _filter_recent_days(allocation_history, days=30)

    # Strip LLM data except last entry
    recent_history = _strip_llm_data_except_last(recent_history)

    compact["allocationHistory"] = recent_history

    # Update profitHistory to match
    profit_history = compact.get("profitHistory", [])
    if profit_history and recent_history:
        # Get timestamps from recent_history
        recent_timestamps = {s["timestamp"] for s in recent_history}
        compact["profitHistory"] = [
            p for p in profit_history if p.get("timestamp") in recent_timestamps
        ]

    # Keep original trades count (total historical trades, not just recent 30 days)
    compact["trades"] = original_trades_count

    return compact


def _create_model_data(agent, account, market_type):
    """Create model data for a single agent."""
    account_data = account.get_account_data()
    model_id = f"{agent.model_name.lower().replace(' ', '-')}-{market_type}"

    portfolio = account_data.get("portfolio")
    allocation_history = account_data.get("allocation_history", [])
    asset_allocation = portfolio.get("current_allocations")

    model = {
        "id": model_id,
        "name": agent.name,
        "category": market_type,
        "status": "active",
        "performance": account_data.get("performance", 0),
        "profit": account_data.get("profit", 0),
        "trades": len(allocation_history),
        "asset_allocation": asset_allocation,
        "portfolio": portfolio,
        "profitHistory": [
            {
                "timestamp": snapshot["timestamp"],
                "profit": snapshot["profit"],
                "totalValue": snapshot["total_value"],
            }
            for snapshot in allocation_history
        ],
        "allocationHistory": allocation_history,
    }
    return model


def _serialize_positions(model_data):
    """Serialize Position objects to dictionaries."""
    if "portfolio" in model_data and "positions" in model_data["portfolio"]:
        model_data["portfolio"]["positions"] = {
            symbol: asdict(p) if isinstance(p, Position) else p
            for symbol, p in model_data["portfolio"]["positions"].items()
        }
    return model_data


def load_historical_data_to_accounts(stock_system, polymarket_system, bitmex_system=None):
    """Load historical data to account memory on every startup.

    This function ALWAYS loads data to restore account state, regardless of whether
    models_data.json exists. The existence of models_data.json is only checked to
    decide whether to run load_backtest_as_initial_data() in main.py.
    """
    # Try to load from hist file first (contains full data), fallback to init file
    source_file = None
    if os.path.exists(MODELS_DATA_HIST_FILE):
        source_file = MODELS_DATA_HIST_FILE
        print("📚 Loading from historical data file (complete data)...")
    elif os.path.exists(MODELS_DATA_INIT_FILE):
        source_file = MODELS_DATA_INIT_FILE
        print("📄 Loading from init file...")
    else:
        print("📄 No historical data file found, starting fresh")
        return

    print("🔄 Loading historical data to account memory...")

    try:
        with open(source_file, "r") as f:
            historical_data = json.load(f)

        print(f"📊 Loading historical data for {len(historical_data)} models...")

        for model_data in historical_data:
            model_name = model_data.get("name", "")
            category = model_data.get("category", "")

            # Skip benchmark models - they will be preserved separately
            if category == "benchmark":
                print(f"  📊 {model_name}: Benchmark model (will be preserved)")
                continue

            if category == "stock":
                system = stock_system
            elif category == "polymarket":
                system = polymarket_system
            elif category == "bitmex" and bitmex_system is not None:
                system = bitmex_system
            else:
                continue

            account = None
            for agent_name, acc in system.accounts.items():
                if agent_name == model_name:
                    account = acc
                    break

            if account:
                restore_account_from_historical_data(account, model_data)
                allocation_count = len(model_data.get("allocationHistory", []))
                print(f"  ✅ {model_name}: {allocation_count} trades loaded")
            else:
                print(f"  ⚠️ {model_name}: Account not found")

    except Exception as e:
        print(f"❌ Failed to load historical data: {e}")


def restore_account_from_historical_data(account, historical_model_data):
    portfolio = historical_model_data.get("portfolio", {})
    account.cash_balance = portfolio.get("cash", account.initial_cash)

    historical_positions = portfolio.get("positions", {})
    for symbol, pos_data in historical_positions.items():
        position = Position(
            symbol=pos_data["symbol"],
            quantity=pos_data["quantity"],
            average_price=pos_data["average_price"],
            current_price=pos_data["current_price"],
            url=pos_data.get("url"),
        )
        account.positions[symbol] = position

    account.target_allocations = portfolio.get("target_allocations", {})

    account.allocation_history = historical_model_data.get("allocationHistory", [])

    account.total_fees = historical_model_data.get("total_fees", 0.0)


def generate_models_data(stock_system, polymarket_system, bitmex_system=None) -> None:
    """Generate and save model data for all systems"""
    try:
        print("🚀 Starting data generation for all markets...")
        all_market_data = []

        existing_benchmarks = _preserve_existing_benchmarks()

        systems = {"stock": stock_system, "polymarket": polymarket_system}
        if bitmex_system is not None:
            systems["bitmex"] = bitmex_system

        for market_type, system in systems.items():
            print(f"--- Processing {market_type.upper()} market ---")
            system.run_cycle()

            for agent_name, account in system.accounts.items():
                agent = system.agents.get(agent_name)
                if not agent:
                    continue

                model_data = _create_model_data(agent, account, market_type)
                model_data_serialized = _serialize_positions(model_data)
                all_market_data.append(model_data_serialized)

                trades_count = len(account.allocation_history)
                print(f"✅ Generated data for {agent_name}: {trades_count} total trades")

        # 添加保留的benchmark模型
        all_market_data.extend(existing_benchmarks)

        # Write full historical data (for backend reload)
        with open(MODELS_DATA_HIST_FILE, "w") as f:
            json.dump(all_market_data, f, indent=4)
        print(f"💾 Saved complete historical data to {MODELS_DATA_HIST_FILE}")

        # Create compact data for frontend (30 days + last LLM only)
        compact_data = [_create_compact_model_data(model) for model in all_market_data]
        with open(MODELS_DATA_FILE, "w") as f:
            json.dump(compact_data, f, indent=4)
        print(f"💾 Saved compact frontend data to {MODELS_DATA_FILE}")

        total_models = len(all_market_data)
        benchmark_count = len(existing_benchmarks)
        print(
            f"🎉 Successfully generated data for {total_models} models ({benchmark_count} benchmarks preserved)"
        )

    except Exception as e:
        print(f"❌ Failed to generate models data: {e}")
        raise


def _preserve_existing_benchmarks():
    """保留现有的benchmark模型，避免被trading cycle覆盖"""
    try:
        # Try to read from hist file first (contains full data)
        source_file = (
            MODELS_DATA_HIST_FILE
            if os.path.exists(MODELS_DATA_HIST_FILE)
            else MODELS_DATA_FILE
        )

        if not os.path.exists(source_file):
            return []

        with open(source_file, "r") as f:
            existing_data = json.load(f)

        # 筛选出benchmark模型 (QQQ/VOO)
        benchmarks = [
            model
            for model in existing_data
            if model.get("id") in ["qqq-benchmark", "voo-benchmark"]
        ]

        if benchmarks:
            print(f"📊 Preserving {len(benchmarks)} existing benchmark models")

        return benchmarks

    except Exception as e:
        print(f"⚠️ Failed to preserve benchmarks: {e}")
        return []


if __name__ == "__main__":
    generate_models_data()

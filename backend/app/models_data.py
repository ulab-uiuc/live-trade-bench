import json
import os
from dataclasses import asdict
from typing import Any, Dict

from live_trade_bench.accounts.base_account import Position

from .config import MODELS_DATA_FILE


def _create_model_data(agent, account, market_type):
    """Create model data for a single agent."""
    account_data = account.get_account_data()
    model_id = f"{agent.model_name.lower().replace(' ', '-')}-{market_type}"

    portfolio = account_data.get("portfolio")
    allocation_history = account_data.get("allocation_history", [])
    asset_allocation = portfolio.get("current_allocations")

    # No processing needed - data should already be in correct format from the system

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
        "chartData": {
            "profit_history": [
                {
                    "timestamp": snapshot["timestamp"],
                    "profit": snapshot["profit"],
                    "totalValue": snapshot["total_value"],
                }
                for snapshot in allocation_history
            ]
        },
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


def merge_model_data(
    existing_model: Dict[str, Any], new_model: Dict[str, Any]
) -> Dict[str, Any]:
    """Merge existing model data with new data, appending historical records."""
    merged = existing_model.copy()

    merged["trades"] = existing_model.get("trades", 0) + new_model.get("trades", 0)

    merged["performance"] = existing_model.get("performance", 0) + new_model.get(
        "performance", 0
    )
    merged["profit"] = existing_model.get("profit", 0) + new_model.get("profit", 0)

    merged["portfolio"] = new_model.get("portfolio", existing_model.get("portfolio"))
    merged["asset_allocation"] = new_model.get(
        "asset_allocation", existing_model.get("asset_allocation")
    )

    existing_allocation_history = existing_model.get("allocationHistory", [])
    new_allocation_history = new_model.get("allocationHistory", [])
    merged["allocationHistory"] = existing_allocation_history + new_allocation_history

    existing_chart_data = existing_model.get("chartData", {})
    new_chart_data = new_model.get("chartData", {})

    existing_profit_history = existing_chart_data.get("profit_history", [])
    new_profit_history = new_chart_data.get("profit_history", [])

    merged["chartData"] = (
        new_chart_data.copy() if new_chart_data else existing_chart_data.copy()
    )

    # ✅ Fix profit_history cumulative calculation
    if existing_profit_history and new_profit_history:
        # Get the last profit value from existing history as base
        base_profit = existing_profit_history[-1]["profit"]
        base_total_value = existing_profit_history[-1]["totalValue"]

        # Adjust new profit history to be cumulative
        adjusted_new_history = []
        for entry in new_profit_history:
            adjusted_entry = entry.copy()
            # Add the base profit to make it cumulative
            adjusted_entry["profit"] = entry["profit"] + base_profit
            # Also adjust totalValue to maintain consistency
            adjusted_entry["totalValue"] = entry["totalValue"] + (
                base_total_value - entry.get("profit", 0) + base_profit
            )
            adjusted_new_history.append(adjusted_entry)

        merged["chartData"]["profit_history"] = (
            existing_profit_history + adjusted_new_history
        )
    else:
        # If no existing history or no new history, just concatenate
        merged["chartData"]["profit_history"] = (
            existing_profit_history + new_profit_history
        )

    return merged


def generate_models_data(stock_system, polymarket_system) -> None:
    """Generate and save model data for all systems."""
    try:
        print("🚀 Starting data generation for both markets...")
        all_market_data = []

        systems = {"stock": stock_system, "polymarket": polymarket_system}

        for market_type, system in systems.items():
            print(f"--- Processing {market_type.upper()} market ---")
            system.run_cycle()

            for agent_name, account in system.accounts.items():
                agent = system.agents.get(agent_name)
                if not agent:
                    continue

                # Check if LLM allocation was successful by looking at allocation history
                account_data = account.get_account_data()
                allocation_history = account_data.get("allocation_history")

                # If no allocation history, or last allocation has no valid allocations, skip
                if not allocation_history:
                    print(f"⚠️ Skipping {agent_name}: No allocation history")
                    continue

                last_allocation = allocation_history[-1].get("allocations")
                if not last_allocation or all(
                    v == 0
                    for v in last_allocation.values()
                    if isinstance(v, (int, float))
                ):
                    print(
                        f"⚠️ Skipping {agent_name}: LLM failed in last cycle (empty allocation)"
                    )
                    continue

                model_data = _create_model_data(agent, account, market_type)
                all_market_data.append(model_data)

        # Try to load existing data for merging
        existing_data = []
        if os.path.exists(MODELS_DATA_FILE):
            try:
                with open(MODELS_DATA_FILE, "r") as f:
                    existing_data = json.load(f)
                print(f"📖 Loaded existing data with {len(existing_data)} models")
            except Exception as e:
                print(f"⚠️ Could not load existing data: {e}, starting fresh")
                existing_data = []

        # Merge new data with existing data
        merged_data = []
        processed_ids = set()

        # First, process all new successful models
        for new_model in all_market_data:
            new_model_serialized = _serialize_positions(new_model)
            model_id = new_model_serialized.get("id")
            processed_ids.add(model_id)

            # Find matching existing model by ID
            existing_model = None
            for existing in existing_data:
                if existing.get("id") == model_id:
                    existing_model = existing
                    break

            if existing_model:
                merged_model = merge_model_data(existing_model, new_model_serialized)
                merged_data.append(merged_model)
                print(
                    f"🔄 Merged data for {new_model_serialized.get('name', 'Unknown')}"
                )
            else:
                merged_data.append(new_model_serialized)
                print(
                    f"➕ Added new model {new_model_serialized.get('name', 'Unknown')}"
                )

        # Then, preserve existing models that weren't updated (LLM failed cases)
        for existing_model in existing_data:
            existing_id = existing_model.get("id")
            if existing_id not in processed_ids:
                merged_data.append(existing_model)
                print(
                    f"📋 Preserved existing data for {existing_model.get('name', 'Unknown')} (no update)"
                )

        # Save merged data (including preserved existing data)
        with open(MODELS_DATA_FILE, "w") as f:
            json.dump(merged_data, f, indent=4)
        print(
            f"✅ Successfully wrote merged data for {len(merged_data)} models to {MODELS_DATA_FILE}"
        )

    except Exception as e:
        print(f"❌ CRITICAL: generate_models_data failed completely: {e}")
        import traceback

        traceback.print_exc()
        print("🔄 Scheduler will continue with next cycle...")


if __name__ == "__main__":
    generate_models_data()

import json
import os
from dataclasses import asdict
from typing import Any, Dict

from live_trade_bench.accounts.base_account import Position

from .config import MODELS_DATA_FILE


def _process_polymarket_positions(positions, market_info):
    """Process Polymarket positions to add question, URL, and category."""
    processed = {}
    for symbol, position in positions.items():
        if "_" in symbol:
            market_id = symbol.split("_")[0]
            if market_id in market_info:
                market_data = market_info[market_id]
                position_dict = (
                    asdict(position)
                    if hasattr(position, "__dataclass_fields__")
                    else position
                )
                processed[symbol] = {
                    **position_dict,
                    "question": market_data.get("question", market_id),
                    "url": market_data.get("url"),
                    "category": market_data.get("category", "Unknown"),
                }
            else:
                processed[symbol] = (
                    asdict(position)
                    if hasattr(position, "__dataclass_fields__")
                    else position
                )
        else:
            processed[symbol] = (
                asdict(position)
                if hasattr(position, "__dataclass_fields__")
                else position
            )
    return processed


def _create_model_data(agent, account, market_type, market_info=None):
    """Create model data for a single agent."""
    account_data = account.get_account_data()
    model_id = f"{agent.model_name.lower().replace(' ', '-')}-{market_type}"

    # Process portfolio positions for Polymarket
    portfolio = account_data.get("portfolio", {})
    if market_type == "polymarket" and "positions" in portfolio and market_info:
        portfolio["positions"] = _process_polymarket_positions(
            portfolio["positions"], market_info
        )

        # Helper to build display key: "<question> YES/NO"
        def _display_key(symbol: str) -> str:
            if "_" in symbol:
                market_id, outcome = symbol.split("_", 1)
                question = market_info.get(market_id, {}).get("question", market_id)
                return f"{question} {outcome.upper()}"
            return symbol

        # 1) Remap positions keys to use question-based keys
        remapped_positions = {}
        for symbol, pos in portfolio.get("positions", {}).items():
            new_key = _display_key(symbol)
            # ensure symbol inside the position matches display key
            if isinstance(pos, dict):
                pos = {**pos, "symbol": new_key}
            remapped_positions[new_key] = pos
        portfolio["positions"] = remapped_positions

        # 2) Remap portfolio allocations (target/current)
        for alloc_field in ("target_allocations", "current_allocations"):
            if alloc_field in portfolio and isinstance(portfolio[alloc_field], dict):
                original_alloc = portfolio[alloc_field]
                portfolio[alloc_field] = {
                    _display_key(k): v for k, v in original_alloc.items()
                }

        # 3) Prepare remapped asset_allocation from current_allocations
        remapped_asset_allocation = portfolio.get("current_allocations", {})

    model = {
        "id": model_id,
        "name": agent.name,
        "category": market_type,
        "status": "active",
        "performance": account_data.get("performance", 0),
        "profit": account_data.get("profit", 0),
        "trades": len(account_data.get("allocation_history", [])),
        "asset_allocation": (
            remapped_asset_allocation
            if market_type == "polymarket"
            else account_data.get("portfolio", {}).get("current_allocations", {})
        ),
        "portfolio": portfolio,
        "chartData": {
            "profit_history": [
                {
                    "timestamp": snapshot["timestamp"],
                    "profit": snapshot["profit"],
                    "totalValue": snapshot["total_value"],
                }
                for snapshot in account_data.get("allocation_history", [])
            ]
        },
        "allocationHistory": account_data.get("allocation_history", []),
    }
    if market_type == "polymarket":
        # Build union of all display keys across history to backfill zeros
        all_display_meta: Dict[str, Dict[str, Any]] = {}
        for snapshot in account_data.get("allocation_history", []):
            alloc = snapshot.get("allocations", {})
            for symbol in alloc.keys():
                if symbol == "CASH":
                    continue
                display_key = _display_key(symbol)
                if display_key not in all_display_meta:
                    url = None
                    category = None
                    if "_" in symbol:
                        market_id = symbol.split("_", 1)[0]
                        mi = (market_info or {}).get(market_id, {})
                        url = mi.get("url")
                        category = mi.get("category", "Unknown")
                    all_display_meta[display_key] = {"url": url, "category": category}

        # Remap allocationHistory: inline url/category into allocations array for direct frontend use
        remapped_history = []
        for snapshot in model["allocationHistory"]:
            if (
                isinstance(snapshot, dict)
                and "allocations" in snapshot
                and isinstance(snapshot["allocations"], dict)
            ):
                alloc = snapshot["allocations"]
                alloc_list = []
                present_names = set()
                for symbol, weight in alloc.items():
                    display_key = _display_key(symbol)
                    url = None
                    category = None
                    if "_" in symbol:
                        market_id = symbol.split("_", 1)[0]
                        mi = (market_info or {}).get(market_id, {})
                        url = mi.get("url")
                        category = mi.get("category", "Unknown")
                    present_names.add(display_key)
                    alloc_list.append(
                        {
                            "name": display_key,
                            "weight": weight,
                            "url": url,
                            "category": category,
                        }
                    )
                # Backfill zero weights for assets seen in other snapshots
                for name, meta in all_display_meta.items():
                    if name not in present_names:
                        alloc_list.append(
                            {
                                "name": name,
                                "weight": 0.0,
                                "url": meta.get("url"),
                                "category": meta.get("category"),
                            }
                        )
                new_snapshot = {**snapshot, "allocations": alloc_list}
                remapped_history.append(new_snapshot)
            else:
                remapped_history.append(snapshot)
        model["allocationHistory"] = remapped_history
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

    merged["portfolio"] = new_model.get("portfolio", {})
    merged["asset_allocation"] = new_model.get("asset_allocation", {})

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
    merged["chartData"]["profit_history"] = existing_profit_history + new_profit_history

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

            # Get market info for Polymarket
            market_info = (
                system.market_info
                if market_type == "polymarket" and hasattr(system, "market_info")
                else None
            )

            for agent_name, account in system.accounts.items():
                agent = system.agents.get(agent_name)
                if not agent:
                    continue

                model_data = _create_model_data(
                    agent, account, market_type, market_info
                )
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
        for new_model in all_market_data:
            new_model_serialized = _serialize_positions(new_model)

            # Find matching existing model by ID
            existing_model = None
            for existing in existing_data:
                if existing.get("id") == new_model_serialized.get("id"):
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

        # Save merged data
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

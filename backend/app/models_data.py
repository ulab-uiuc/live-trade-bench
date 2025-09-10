import json
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dataclasses import asdict

from live_trade_bench.accounts.base_account import Position

from .config import MODELS_DATA_FILE


def _create_model_data(agent, account, market_type):
    """Create model data for a single agent."""
    account_data = account.get_account_data()
    model_id = f"{agent.model_name.lower().replace(' ', '-')}-{market_type}"

    portfolio = account_data.get("portfolio", {})
    allocation_history = account_data.get("allocation_history", [])
    asset_allocation = portfolio.get("current_allocations", {})

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

                model_data = _create_model_data(agent, account, market_type)
                all_market_data.append(model_data)

        # Serialize and save data
        serializable_data = [_serialize_positions(model) for model in all_market_data]

        with open(MODELS_DATA_FILE, "w") as f:
            json.dump(serializable_data, f, indent=4)
        print(
            f"✅ Successfully wrote data for {len(all_market_data)} models to {MODELS_DATA_FILE}"
        )

    except Exception as e:
        print(f"❌ CRITICAL: generate_models_data failed completely: {e}")
        import traceback

        traceback.print_exc()
        print("🔄 Scheduler will continue with next cycle...")


if __name__ == "__main__":
    generate_models_data()

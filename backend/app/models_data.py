import json
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dataclasses import asdict

from live_trade_bench.accounts.base_account import Position
from live_trade_bench.systems import PolymarketPortfolioSystem, StockPortfolioSystem

from .config import MODELS_DATA_FILE, get_base_model_configs


def generate_models_data() -> None:
    print("🚀 Starting data generation for both markets...")
    all_market_data = []

    for market_type in ["stock", "polymarket"]:
        print(f"--- Processing {market_type.upper()} market ---")
        system = (
            StockPortfolioSystem.get_instance()
            if market_type == "stock"
            else PolymarketPortfolioSystem.get_instance()
        )

        if not system.agents:
            print(
                f"--- No agents found for {market_type}. Adding agents from config. ---"
            )
            model_configs = get_base_model_configs()
            initial_cash = 1000.0 if market_type == "stock" else 500.0
            for display_name, model_id in model_configs:
                system.add_agent(display_name, initial_cash, model_id)

        system.initialize_for_live()
        system.run_cycle()

        for agent_name, account in system.accounts.items():
            agent = system.agents.get(agent_name)
            if not agent:
                continue

            account_data = account.get_account_data()
            model_id = f"{agent.model_name.lower().replace(' ', '-')}-{market_type}"

            model_data = {
                "id": model_id,
                "name": agent.name,
                "category": market_type,
                "status": "active",  # Assuming active status for now
                "performance": account_data.get("performance", 0),
                "profit": account_data.get("profit", 0),
                "trades": account_data.get("trades", 0),
                "asset_allocation": account_data.get("portfolio", {}).get(
                    "current_allocations", {}
                ),
                "portfolio": account_data.get("portfolio", {}),
                "chartData": {"profit_history": []},  # Placeholder for chart data
                "allocationHistory": account_data.get("allocation_history", []),
            }
            all_market_data.append(model_data)

    # Manually serialize any dataclass objects before writing to JSON
    serializable_data = []
    for model in all_market_data:
        serializable_model = model.copy()
        if (
            "portfolio" in serializable_model
            and "positions" in serializable_model["portfolio"]
        ):
            serializable_model["portfolio"]["positions"] = {
                symbol: asdict(p) if isinstance(p, Position) else p
                for symbol, p in serializable_model["portfolio"]["positions"].items()
            }
        serializable_data.append(serializable_model)

    try:
        with open(MODELS_DATA_FILE, "w") as f:
            json.dump(serializable_data, f, indent=4)
        print(
            f"✅ Successfully wrote data for {len(all_market_data)} models to {MODELS_DATA_FILE}"
        )
    except IOError as e:
        print(f"❌ Error writing to {MODELS_DATA_FILE}: {e}")


if __name__ == "__main__":
    generate_models_data()

import json
import os
import sys
from datetime import datetime

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from .config import SYSTEM_DATA_FILE, TRADING_CONFIG, get_base_model_configs
from .system_factory import get_system


def update_system_status() -> None:
    print("📊 Updating system status...")
    try:
        # Create fresh, mock-aware, thread-safe instances
        stock_system = get_system("stock")
        polymarket_system = get_system("polymarket")

        model_configs = get_base_model_configs()
        for display_name, model_id in model_configs:
            stock_system.add_agent(
                display_name, TRADING_CONFIG["initial_cash_stock"], model_id
            )
            polymarket_system.add_agent(
                display_name, TRADING_CONFIG["initial_cash_polymarket"], model_id
            )

        stock_count = len(stock_system.agents)
        poly_count = len(polymarket_system.agents)
        total_value_stock = sum(
            acc.get_total_value() for acc in stock_system.accounts.values()
        )
        total_value_poly = sum(
            acc.get_total_value() for acc in polymarket_system.accounts.values()
        )

        status = {
            "timestamp": datetime.now().isoformat(),
            "status": "running",
            "stock_agents": stock_count,
            "polymarket_agents": poly_count,
            "total_agents": stock_count + poly_count,
            "total_value_stock": total_value_stock,
            "total_value_polymarket": total_value_poly,
            "combined_total_value": total_value_stock + total_value_poly,
        }

        with open(SYSTEM_DATA_FILE, "w") as f:
            json.dump(status, f, indent=4)
        print(f"✅ System status updated and saved to {SYSTEM_DATA_FILE}")

    except Exception as e:
        print(f"❌ Error updating system status: {e}")


if __name__ == "__main__":
    update_system_status()

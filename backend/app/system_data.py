import json
import os
import sys
from datetime import datetime

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from live_trade_bench.systems import PolymarketPortfolioSystem, StockPortfolioSystem

from .config import SYSTEM_DATA_FILE


def update_system_status() -> None:
    print("📊 Updating system status...")

    try:
        stock_system = StockPortfolioSystem.get_instance()
        polymarket_system = PolymarketPortfolioSystem.get_instance()

        stock_agents = len(stock_system.agents)
        polymarket_agents = len(polymarket_system.agents)

        status_data = {
            "running": True,
            "total_agents": stock_agents + polymarket_agents,
            "stock_agents": stock_agents,
            "polymarket_agents": polymarket_agents,
            "last_updated": datetime.now().isoformat(),
        }

        with open(SYSTEM_DATA_FILE, "w") as f:
            json.dump(status_data, f, indent=4)
        print(f"✅ System status updated and saved to {SYSTEM_DATA_FILE}")

    except Exception as e:
        print(f"❌ Error updating system status: {e}")


if __name__ == "__main__":
    update_system_status()

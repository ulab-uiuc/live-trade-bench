import json
import os
import sys
from datetime import datetime

from live_trade_bench.systems import (
    BitMEXPortfolioSystem,
    ForexPortfolioSystem,
    PolymarketPortfolioSystem,
    StockPortfolioSystem,
)

from .config import SYSTEM_DATA_FILE, TRADING_CONFIG, get_base_model_configs

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def update_system_status() -> None:
    print("📊 Updating system status...")
    try:
        stock_system = StockPortfolioSystem.get_instance()
        polymarket_system = PolymarketPortfolioSystem.get_instance()
        bitmex_system = BitMEXPortfolioSystem.get_instance()
        forex_system = ForexPortfolioSystem.get_instance()

        model_configs = get_base_model_configs()
        for display_name, model_id in model_configs:
            # Only add if missing to avoid resetting existing accounts
            if display_name not in stock_system.agents:
                stock_system.add_agent(
                    display_name, TRADING_CONFIG["initial_cash_stock"], model_id
                )
            if display_name not in polymarket_system.agents:
                polymarket_system.add_agent(
                    display_name, TRADING_CONFIG["initial_cash_polymarket"], model_id
                )
            if display_name not in bitmex_system.agents:
                bitmex_system.add_agent(
                    display_name, TRADING_CONFIG["initial_cash_bitmex"], model_id
                )
            if display_name not in forex_system.agents:
                forex_system.add_agent(
                    display_name, TRADING_CONFIG["initial_cash_forex"], model_id
                )

        stock_count = len(stock_system.agents)
        poly_count = len(polymarket_system.agents)
        bitmex_count = len(bitmex_system.agents)
        forex_count = len(forex_system.agents)
        total_value_stock = sum(
            acc.get_total_value() for acc in stock_system.accounts.values()
        )
        total_value_poly = sum(
            acc.get_total_value() for acc in polymarket_system.accounts.values()
        )
        total_value_bitmex = sum(
            acc.get_total_value() for acc in bitmex_system.accounts.values()
        )
        total_value_forex = sum(
            acc.get_total_value() for acc in forex_system.accounts.values()
        )

        status = {
            "timestamp": datetime.now().isoformat(),
            "status": "running",
            "stock_agents": stock_count,
            "polymarket_agents": poly_count,
            "bitmex_agents": bitmex_count,
            "forex_agents": forex_count,
            "total_agents": stock_count + poly_count + bitmex_count + forex_count,
            "total_value_stock": total_value_stock,
            "total_value_polymarket": total_value_poly,
            "total_value_bitmex": total_value_bitmex,
            "total_value_forex": total_value_forex,
            "combined_total_value": (
                total_value_stock
                + total_value_poly
                + total_value_bitmex
                + total_value_forex
            ),
        }

        with open(SYSTEM_DATA_FILE, "w") as f:
            json.dump(status, f, indent=4)
        print(f"✅ System status updated and saved to {SYSTEM_DATA_FILE}")

    except Exception as e:
        print(f"❌ Error updating system status: {e}")


if __name__ == "__main__":
    update_system_status()

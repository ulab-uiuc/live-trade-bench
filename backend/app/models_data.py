import json
import os
import sys
from typing import Any, Dict

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.app.config import MODELS_DATA_FILE
from live_trade_bench.systems import (
    PolymarketPortfolioSystem,
    StockPortfolioSystem,
)

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

        system.run_cycle()

        for agent_name, account in system.accounts.items():
            agent = system.agents.get(agent_name)
            if not agent:
                continue

            account_data = account.get_account_data()
            
            model_data = {
                "model_name": agent.name,
                "model_id": agent.model_name,
                "market_type": market_type,
                **account_data,
            }
            all_market_data.append(model_data)
    
    try:
        with open(MODELS_DATA_FILE, "w") as f:
            json.dump(all_market_data, f, indent=4)
        print(f"✅ Successfully wrote data for {len(all_market_data)} models to {MODELS_DATA_FILE}")
    except IOError as e:
        print(f"❌ Error writing to {MODELS_DATA_FILE}: {e}")

def run_backend_backtest() -> None:
    from datetime import datetime, timedelta
    from backend.app.config import (
        BACKTEST_RESULTS_FILE,
        get_base_model_configs,
    )
    from live_trade_bench.backtesting import run_backtest

    print("🚀 Starting backend backtest...")
    models = get_base_model_configs()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    all_results = {}
    for market_type in ["stock", "polymarket"]:
        print(f"--- Running backtest for {market_type.upper()} market ---")
        initial_cash = 1000.0 if market_type == "stock" else 500.0
        
        results = run_backtest(
            models=models,
            initial_cash=initial_cash,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            market_type=market_type,
        )
        all_results[market_type] = results

    try:
        with open(BACKTEST_RESULTS_FILE, "w") as f:
            json.dump(all_results, f, indent=4)
        print(f"✅ Backtest results saved to {BACKTEST_RESULTS_FILE}")
    except IOError as e:
        print(f"❌ Error writing backtest results: {e}")

if __name__ == "__main__":
    generate_models_data()

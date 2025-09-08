import json
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from live_trade_bench.mock.mock_system import (  # noqa: E402
    MockAgentFetcherPolymarketSystem,
    MockAgentFetcherStockSystem,
    MockAgentPolymarketSystem,
    MockAgentStockSystem,
    MockFetcherPolymarketSystem,
    MockFetcherStockSystem,
)
from live_trade_bench.systems.polymarket_system import (  # noqa: E402
    PolymarketPortfolioSystem,
)
from live_trade_bench.systems.stock_system import StockPortfolioSystem  # noqa: E402

from .config import (  # noqa: E402
    MODELS_DATA_FILE,
    POLYMARKET_MOCK_MODE,
    STOCK_MOCK_MODE,
    MockMode,
)


def get_stock_system():
    if STOCK_MOCK_MODE == MockMode.MOCK_AGENTS:
        return MockAgentStockSystem.get_instance()
    if STOCK_MOCK_MODE == MockMode.MOCK_FETCHERS:
        return MockFetcherStockSystem.get_instance()
    if STOCK_MOCK_MODE == MockMode.MOCK_AGENTS_AND_FETCHERS:
        return MockAgentFetcherStockSystem.get_instance()
    return StockPortfolioSystem.get_instance()


def get_polymarket_system():
    if POLYMARKET_MOCK_MODE == MockMode.MOCK_AGENTS:
        return MockAgentPolymarketSystem.get_instance()
    if POLYMARKET_MOCK_MODE == MockMode.MOCK_FETCHERS:
        return MockFetcherPolymarketSystem.get_instance()
    if POLYMARKET_MOCK_MODE == MockMode.MOCK_AGENTS_AND_FETCHERS:
        return MockAgentFetcherPolymarketSystem.get_instance()
    return PolymarketPortfolioSystem.get_instance()


def generate_models_data() -> None:
    print("🚀 Starting data generation for both markets...")
    all_market_data = []

    for market_type in ["stock", "polymarket"]:
        print(f"--- Processing {market_type.upper()} market ---")
        system = (
            get_stock_system() if market_type == "stock" else get_polymarket_system()
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
        print(
            f"✅ Successfully wrote data for {len(all_market_data)} models to {MODELS_DATA_FILE}"
        )
    except IOError as e:
        print(f"❌ Error writing to {MODELS_DATA_FILE}: {e}")


if __name__ == "__main__":
    generate_models_data()

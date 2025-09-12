import json
import os
from dataclasses import asdict

from live_trade_bench.accounts.base_account import Position

from .config import MODELS_DATA_FILE, MODELS_DATA_INIT_FILE


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


def load_historical_data_to_accounts(stock_system, polymarket_system):
    if not os.path.exists(MODELS_DATA_INIT_FILE):
        print("📄 No historical data file found, starting fresh")
        return

    if os.path.exists(MODELS_DATA_FILE):
        print("📋 Models data file already exists, skipping historical data loading")
        return

    print("🆕 First startup detected - loading historical data to account memory...")

    try:
        with open(MODELS_DATA_INIT_FILE, "r") as f:
            historical_data = json.load(f)

        print(f"📊 Loading historical data for {len(historical_data)} models...")

        for model_data in historical_data:
            model_name = model_data.get("name", "")
            category = model_data.get("category", "")

            system = stock_system if category == "stock" else polymarket_system

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


def generate_models_data(stock_system, polymarket_system) -> None:
    """Generate and save model data for all systems"""
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
                model_data_serialized = _serialize_positions(model_data)
                all_market_data.append(model_data_serialized)

                trades_count = len(account.allocation_history)
                print(f"✅ Generated data for {agent_name}: {trades_count} total trades")

        with open(MODELS_DATA_FILE, "w") as f:
            json.dump(all_market_data, f, indent=4)

        print(f"🎉 Successfully generated data for {len(all_market_data)} models")

    except Exception as e:
        print(f"❌ Failed to generate models data: {e}")
        raise


if __name__ == "__main__":
    generate_models_data()

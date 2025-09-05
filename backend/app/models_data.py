"""
Real model data provider using live_trade_bench
"""

import os
import random
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

# Add live_trade_bench to path
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, project_root)

from live_trade_bench import (
    create_polymarket_portfolio_system,
    create_stock_portfolio_system,
)
from live_trade_bench.agents.polymarket_system import PolymarketPortfolioSystem
from live_trade_bench.agents.stock_system import StockPortfolioSystem

# Global instances - lazy loaded
_stock_system = None
_polymarket_system = None


def _get_stock_system():
    """Get or create stock system with real agents"""
    stock_system = StockPortfolioSystem.get_instance()
    if not stock_system.agents:
        # Add real LLM agents
        models = [
            ("GPT-4o", "gpt-4o", 1000),
            ("Claude 3.5 Sonnet", "claude-3-5-sonnet-20241022", 1000),
            ("GPT-4 Turbo", "gpt-4-turbo", 1000),
            ("GPT-4o Mini", "gpt-4o-mini", 1000),
            ("Claude 3 Haiku", "claude-3-haiku-20240307", 1000),
            ("Gemini Pro", "gemini-pro", 1000),
            ("Llama 3.1", "llama-3.1-70b-versatile", 1000),
        ]

        for name, model_name, initial_cash in models:
            stock_system.add_agent(
                name=name, initial_cash=initial_cash, model_name=model_name
            )

    return stock_system


def _get_polymarket_system():
    """Get or create polymarket system with real agents"""
    polymarket_system = PolymarketPortfolioSystem.get_instance()
    if not polymarket_system.agents:
        # Add real LLM agents
        models = [
            ("GPT-4o", "gpt-4o", 500),
            ("Claude 3.5 Sonnet", "claude-3-5-sonnet-20241022", 500),
            ("GPT-4 Turbo", "gpt-4-turbo", 500),
            ("GPT-4o Mini", "gpt-4o-mini", 500),
            ("Claude 3 Haiku", "claude-3-haiku-20240307", 500),
            ("Gemini Pro", "gemini-pro", 500),
            ("Llama 3.1", "llama-3.1-70b-versatile", 500),
        ]

        for name, model_name, initial_cash in models:
            polymarket_system.add_agent(
                name=name, initial_cash=initial_cash, model_name=model_name
            )

    return polymarket_system


def _generate_mock_allocation(universe: List[str]) -> Dict[str, float]:
    """Generates a random portfolio allocation for mocking purposes."""
    # Ensure we have a universe to select from, excluding CASH
    non_cash_universe = [asset for asset in universe if asset != "CASH"]
    if not non_cash_universe:
        return {"CASH": 1.0}

    # Pick 1 to 4 assets from the universe to allocate (plus CASH)
    num_assets = random.randint(1, min(4, len(non_cash_universe)))
    selected_assets = random.sample(non_cash_universe, num_assets)

    # Always include CASH
    selected_assets.append("CASH")

    # Generate random weights
    weights = [random.random() for _ in selected_assets]
    total_weight = sum(weights)

    # Normalize weights to sum to 1.0
    allocation = {
        asset: weight / total_weight for asset, weight in zip(selected_assets, weights)
    }

    return allocation


def get_models_data() -> List[Dict[str, Any]]:
    """
    Get comprehensive model data including performance, allocation, and chart data,
    all generated from a single, consistent state.
    """
    models = []

    systems = {
        "stock": {
            "system": _get_stock_system(),
            "initial_cash": 1000.0,
            "accuracy": 75.0,
        },
        "polymarket": {
            "system": _get_polymarket_system(),
            "initial_cash": 500.0,
            "accuracy": 70.0,
        },
    }

    for category, config in systems.items():
        system = config["system"]
        initial_cash = config["initial_cash"]

        for agent_name, agent in system.agents.items():
            account = agent.account
            model_id = f"{agent_name.lower().replace(' ', '-')}_{category}"

            # 1. Simulate portfolio change
            mock_allocation = _generate_mock_allocation(system.universe)
            account._simulate_rebalance_to_target(mock_allocation)
            account._record_allocation_snapshot()

            # 2. Get performance metrics from the new state
            portfolio_breakdown = account.get_portfolio_value_breakdown()
            total_value = portfolio_breakdown.get("total_value", initial_cash)
            return_pct = (
                ((total_value - initial_cash) / initial_cash) * 100
                if initial_cash > 0
                else 0.0
            )
            profit_amount = total_value - initial_cash

            # 3. Get portfolio details (for modal)
            portfolio_details = {
                "cash": account.cash_balance,
                "total_value": total_value,
                "holdings": {
                    symbol: pos.quantity * pos.current_price
                    for symbol, pos in account.positions.items()
                },
                "target_allocations": portfolio_breakdown.get(
                    "current_allocations", {}
                ),
                "return_pct": round(return_pct, 2),
                "unrealized_pnl": round(profit_amount, 2),
            }

            # 4. Generate profit history directly from allocation history for a consistent mock
            profit_history = []
            if account.allocation_history:
                for snapshot in account.allocation_history:
                    value = snapshot["total_value"]
                    profit = value - initial_cash
                    profit_history.append(
                        {
                            "timestamp": snapshot["timestamp"],
                            "profit": round(profit, 2),
                            "totalValue": round(value, 2),
                        }
                    )
            else:  # Fallback for the very first data point
                profit_history.append(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "profit": 0.0,
                        "totalValue": initial_cash,
                    }
                )

            # 5. Get chart data (for modal)
            chart_data = {
                "holdings": portfolio_details["holdings"],
                "profit_history": profit_history,
                "total_value": total_value,
            }

            # 6. Get allocation history (for modal)
            allocation_history = account.allocation_history

            # 7. Assemble the comprehensive model object
            models.append(
                {
                    # Dashboard card data
                    "id": model_id,
                    "name": agent_name,
                    "category": category,
                    "performance": round(return_pct, 2),
                    "profit": round(profit_amount, 2),
                    "trades": len(account.transactions),
                    "status": "active",
                    "asset_allocation": portfolio_breakdown.get(
                        "current_allocations", {}
                    ),
                    # Detailed modal data, nested
                    "portfolio": portfolio_details,
                    "chartData": chart_data,
                    "allocationHistory": allocation_history,
                    "last_updated": "2024-01-01T00:00:00Z",
                }
            )

    return models


def get_system_status() -> Dict[str, Any]:
    """Get real system status from live_trade_bench"""
    stock_system = _get_stock_system()
    polymarket_system = _get_polymarket_system()

    stock_count = len(stock_system.agents)
    poly_count = len(polymarket_system.agents)

    return {
        "running": True,
        "stock_agents": stock_count,
        "polymarket_agents": poly_count,
        "total_agents": stock_count + poly_count,
    }


def get_allocation_history(model_id: str) -> Optional[List[Dict[str, Any]]]:
    """Get the allocation history for a specific model."""
    try:
        # Parse model ID to get agent and system
        if "_stock" in model_id:
            system = _get_stock_system()
            agent_name = model_id.replace("_stock", "").replace("-", " ").title()
        elif "_polymarket" in model_id:
            system = _get_polymarket_system()
            agent_name = model_id.replace("_polymarket", "").replace("-", " ").title()
        else:
            return None

        # Get the agent
        agent = system.agents.get(agent_name)
        if not agent:
            return None

        return agent.account.allocation_history

    except Exception as e:
        print(f"Error getting allocation history for {model_id}: {e}")
        return None


def trigger_cycle() -> Dict[str, Any]:
    """Run one trading cycle using real live_trade_bench systems"""
    try:
        stock_system = _get_stock_system()
        polymarket_system = _get_polymarket_system()

        print("🔄 Triggering LLM trading cycles...")

        # Run stock system cycle
        print("  📈 Running stock portfolio cycle...")
        stock_result = stock_system.run_cycle()

        # Run polymarket system cycle
        print("  🎯 Running polymarket portfolio cycle...")
        poly_result = polymarket_system.run_cycle()

        # Check results
        success = stock_result.get("success", True) and poly_result.get("success", True)

        if success:
            print("✅ LLM trading cycles completed successfully")
            return {
                "status": "success",
                "message": "LLM trading cycles completed successfully",
                "stock_result": stock_result,
                "polymarket_result": poly_result,
            }
        else:
            error_msg = f"Stock: {stock_result.get('error', 'OK')}, Polymarket: {poly_result.get('error', 'OK')}"
            return {"status": "error", "message": f"Some cycles failed: {error_msg}"}

    except Exception as e:
        print(f"❌ Trading cycle failed: {e}")
        import traceback

        traceback.print_exc()
        return {"status": "error", "message": f"Trading cycle failed: {str(e)}"}

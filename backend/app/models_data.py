"""
Real model data provider using live_trade_bench
"""

import json
import os
import random
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any, Dict, List, Optional

# Import after path modification
from live_trade_bench.agents.polymarket_system import (  # noqa: E402
    PolymarketPortfolioSystem,
)
from live_trade_bench.agents.stock_system import StockPortfolioSystem  # noqa: E402
from live_trade_bench.fetchers.stock_fetcher import (  # noqa: E402
    fetch_current_stock_price,
)

# 使用统一配置管理
from .config import MODELS_DATA_FILE, get_base_model_configs


def _save_backtest_data_to_models(backtest_results: Dict[str, Any]):
    """Save backtest data directly into models_data.json instead of separate file."""
    try:
        # Load existing models data
        if os.path.exists(MODELS_DATA_FILE):
            with open(MODELS_DATA_FILE, "r") as f:
                existing_models = json.load(f)
        else:
            existing_models = []

        # Update models with backtest data
        for model in existing_models:
            model_name = model.get("name", "")
            category = model.get("category", "")

            # Find matching backtest data using model name (not id)
            category_results = backtest_results.get(category, {})
            for backtest_model_name, backtest_data in category_results.items():
                # Match by model name (case-insensitive)
                if backtest_model_name.lower() == model_name.lower():
                    # Add backtest data directly to model
                    model["backtest"] = {
                        "initial_value": backtest_data.get("initial_value", 0),
                        "final_value": backtest_data.get("final_value", 0),
                        "return_percentage": backtest_data.get("return_percentage", 0),
                        "period": backtest_data.get("period", ""),
                        "daily_values": backtest_data.get(
                            "daily_values", []
                        ),  # Include daily progression
                    }
                    print(
                        f"✅ Added backtest data to {model['name']}: {backtest_data.get('return_percentage', 0):.2f}%"
                    )
                    break

        # Save updated models data
        with open(MODELS_DATA_FILE, "w") as f:
            json.dump(existing_models, f, indent=2)

        print(f"✅ Backtest data saved directly to {MODELS_DATA_FILE}")

    except Exception as e:
        print(f"⚠️ Failed to save backtest data to models: {e}")


def _get_stock_system():
    """Get or create stock system with real agents"""
    stock_system = StockPortfolioSystem.get_instance()
    if not stock_system.agents:
        # Use centralized model configurations
        base_models = get_base_model_configs()

        for name, model_name in base_models:
            stock_system.add_agent(name=name, initial_cash=1000, model_name=model_name)

    return stock_system


def _get_polymarket_system():
    """Get or create polymarket system with real agents"""
    polymarket_system = PolymarketPortfolioSystem.get_instance()
    if not polymarket_system.agents:
        # Use centralized model configurations
        base_models = get_base_model_configs()

        for name, model_name in base_models:
            polymarket_system.add_agent(
                name=name, initial_cash=500, model_name=model_name
            )

    return polymarket_system


def get_model_configurations():
    """Get model configurations for backtest.

    Returns:
        tuple: (stock_models, polymarket_models) where each is a list of (name, model_id) tuples
    """
    # Use centralized model configurations - single source of truth!
    base_models = get_base_model_configs()

    # Return same models for both markets (only initial_cash differs)
    return base_models, base_models


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

    # Note: Backtest data is now stored directly in models, no separate loading needed
    print("📊 Using integrated backtest data from models")

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

            # 1. Use REAL trading data instead of mock simulation
            # Note: At startup, the systems are fresh, so we rely on backtest data
            # for historical performance and generate minimal current state

            # Get current portfolio state (may be empty on startup)
            portfolio_breakdown = account.get_portfolio_value_breakdown()
            total_value = portfolio_breakdown.get("total_value", initial_cash)
            return_pct = (
                ((total_value - initial_cash) / initial_cash) * 100
                if initial_cash > 0
                else 0.0
            )
            profit_amount = total_value - initial_cash

            # 2. Get portfolio details (for modal) - use actual account state
            portfolio_details = {
                "cash": account.cash_balance,
                "total_value": total_value,
                "holdings": {
                    symbol: pos.quantity * pos.current_price
                    for symbol, pos in account.positions.items()
                },
                "target_allocations": getattr(account, "target_allocations", {}),
                "current_allocations": getattr(
                    account, "get_current_allocations", lambda: lambda: {}
                )(),
                "return_pct": round(return_pct, 2),
                "unrealized_pnl": round(profit_amount, 2),
            }

            # 3. Generate profit history from allocation history OR backtest data
            profit_history = []
            if account.allocation_history:
                # Use real allocation history if available
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
            else:
                # Fallback: use integrated backtest data for initial profit history
                # Note: backtest data is now directly embedded in model objects
                profit_history.append(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "profit": 0.0,
                        "totalValue": initial_cash,
                    }
                )

            # 4. Get chart data (for modal) - use real data
            chart_data = {
                "holdings": portfolio_details["holdings"],
                "profit_history": profit_history,
                "total_value": total_value,
            }

            # 5. Get allocation history (for modal) - use real data
            allocation_history = account.allocation_history

            # 6. Assemble the comprehensive model object using REAL data
            model_obj = {
                # Dashboard card data
                "id": model_id,
                "name": agent_name,
                "category": category,
                "performance": round(return_pct, 2),
                "profit": round(profit_amount, 2),
                "trades": len(account.transactions),
                "status": "active",
                "asset_allocation": getattr(
                    account, "get_current_allocations", lambda: lambda: {}
                )(),
                # Detailed modal data, nested
                "portfolio": portfolio_details,
                "chartData": chart_data,
                "allocationHistory": allocation_history,
                "last_updated": datetime.now().isoformat(),
            }

            # Note: Backtest data is now integrated directly when models are created
            models.append(model_obj)

    # Save to JSON file using centralized config - PRESERVE backtest data
    print(f"Saving {len(models)} models to JSON file...")
    import json

    # Load existing models to preserve backtest data
    existing_models = []
    if os.path.exists(MODELS_DATA_FILE):
        try:
            with open(MODELS_DATA_FILE, "r") as f:
                existing_models = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            existing_models = []

    # Merge backtest data from existing models into new models
    for new_model in models:
        # Find matching existing model
        for existing_model in existing_models:
            if existing_model.get("name") == new_model.get(
                "name"
            ) and existing_model.get("category") == new_model.get("category"):
                # Preserve backtest data if it exists
                if "backtest" in existing_model:
                    new_model["backtest"] = existing_model["backtest"]
                    print(f"✅ Preserved backtest data for {new_model['name']}")
                break

    # Save the updated models to file
    with open(MODELS_DATA_FILE, "w") as f:
        json.dump(models, f, indent=2)
    print("Models saved successfully!")

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


def _parallel_process_agents(stock_system, polymarket_system) -> Dict[str, Any]:
    """并行处理所有智能体的LLM调用 - 复用现有系统接口"""
    print("🚀 Starting parallel system processing using existing interfaces...")

    # 直接调用本地的并行系统处理方法
    result = run_parallel_cycle(stock_system, polymarket_system, for_date=None)

    if result["success"]:
        print("✅ Parallel system processing completed successfully")

        # Initialize all_agents list
        all_agents = []

        # Add stock agents
        for agent_name, agent in stock_system.agents.items():
            all_agents.append(
                {
                    "name": agent_name,
                    "agent": agent,
                    "system": "stock",
                    "system_instance": stock_system,
                }
            )

    # Add polymarket agents
    for agent_name, agent in polymarket_system.agents.items():
        all_agents.append(
            {
                "name": agent_name,
                "agent": agent,
                "system": "polymarket",
                "system_instance": polymarket_system,
            }
        )

    print(f"📊 Processing {len(all_agents)} agents in parallel...")

    # Pre-fetch shared market data to avoid duplicate fetching per agent
    from concurrent.futures import as_completed

    shared_stock_market_data: Dict[str, Dict[str, Any]] = {}
    if getattr(stock_system, "universe", None):
        print("🔎 Pre-fetching stock market data in parallel...")
        tickers = list(stock_system.universe)
        max_ticker_workers = max(2, min(16, len(tickers)))
        with ThreadPoolExecutor(max_workers=max_ticker_workers) as tpool:
            future_to_ticker = {
                tpool.submit(fetch_current_stock_price, ticker): ticker
                for ticker in tickers
            }
            for fut in as_completed(future_to_ticker):
                ticker = future_to_ticker[fut]
                try:
                    price = fut.result()
                    if price:
                        shared_stock_market_data[ticker] = {
                            "ticker": ticker,
                            "name": stock_system.stock_info[ticker]["name"],
                            "sector": stock_system.stock_info[ticker]["sector"],
                            "current_price": price,
                            "market_cap": stock_system.stock_info[ticker]["market_cap"],
                        }
                except Exception as e:
                    print(f"⚠️ Failed to fetch data for {ticker}: {e}")

    print(
        f"📈 Pre-fetched {len(shared_stock_market_data)} stock quotes; sharing across agents"
    )

    # Polymarket can fetch once via its system method
    try:
        shared_polymarket_market_data = polymarket_system._fetch_market_data()
    except Exception as e:
        print(f"⚠️ Failed to pre-fetch polymarket data: {e}")
        shared_polymarket_market_data = {}

    # Function to process a single agent
    def process_single_agent(agent_info):
        try:
            agent_name = agent_info["name"]
            agent = agent_info["agent"]
            system_type = agent_info["system"]
            system_instance = agent_info["system_instance"]

            print(f"🤖 [{system_type.upper()}] {agent_name} starting LLM call...")

            # Get market data based on system type (shared across agents)
            if system_type == "stock":
                market_data = shared_stock_market_data

                # Update position prices with shared data
                for ag in system_instance.agents.values():
                    if hasattr(ag.account, "update_position_price"):
                        for ticker, data in market_data.items():
                            ag.account.update_position_price(
                                ticker, data.get("current_price", 0)
                            )

            else:  # polymarket
                market_data = shared_polymarket_market_data

            if not market_data:
                return {
                    "agent_name": agent_name,
                    "system": system_type,
                    "success": False,
                    "allocation": None,
                }

            # Generate portfolio allocation
            allocation = agent.generate_portfolio_allocation(
                market_data, agent.account, None, news_data=None  # live trading
            )

            if allocation:
                print(
                    f"✅ [{system_type.upper()}] {agent_name} allocation generated successfully"
                )
                return {
                    "agent_name": agent_name,
                    "system": system_type,
                    "success": True,
                    "allocation": allocation,
                }
            else:
                print(
                    f"⚠️ [{system_type.upper()}] {agent_name} no allocation generated"
                )
                return {
                    "agent_name": agent_name,
                    "system": system_type,
                    "success": True,
                    "allocation": None,
                }

        except Exception as e:
            print(f"❌ [{system_type.upper()}] {agent_name} error: {e}")
            import traceback

            traceback.print_exc()
            return {
                "agent_name": agent_name,
                "system": system_type,
                "success": False,
                "error": str(e),
            }

    # Execute all agents in parallel
    results = []
    workers = max(2, min(32, len(all_agents)))
    with ThreadPoolExecutor(max_workers=workers) as executor:
        # Submit all tasks
        future_to_agent = {
            executor.submit(process_single_agent, agent_info): agent_info
            for agent_info in all_agents
        }
        for future in as_completed(future_to_agent):
            agent_info = future_to_agent[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"❌ Task failed for {agent_info['name']}: {e}")
                results.append(
                    {
                        "agent_name": agent_info["name"],
                        "system": agent_info["system"],
                        "success": False,
                        "error": str(e),
                    }
                )

    # Group results by system
    stock_results = [r for r in results if r["system"] == "stock"]
    polymarket_results = [r for r in results if r["system"] == "polymarket"]

    return {
        "success": True,
        "total_agents": len(results),
        "stock_success": len([r for r in stock_results if r["success"]]),
        "polymarket_success": len([r for r in polymarket_results if r["success"]]),
        "results": results,
    }

    shared_stock_market_data: Dict[str, Dict[str, Any]] = {}
    if getattr(stock_system, "universe", None):
        print("🔎 Pre-fetching stock market data in parallel...")
        tickers = list(stock_system.universe)
        max_ticker_workers = max(2, min(16, len(tickers)))
        with ThreadPoolExecutor(max_workers=max_ticker_workers) as tpool:
            future_to_ticker = {
                tpool.submit(fetch_current_stock_price, ticker): ticker
                for ticker in tickers
            }
            for fut in as_completed(future_to_ticker):
                ticker = future_to_ticker[fut]
                try:
                    price = fut.result()
                    if price:
                        shared_stock_market_data[ticker] = {
                            "ticker": ticker,
                            "name": stock_system.stock_info[ticker]["name"],
                            "sector": stock_system.stock_info[ticker]["sector"],
                            "current_price": price,
                            "market_cap": stock_system.stock_info[ticker]["market_cap"],
                        }
                except Exception as e:
                    print(f"⚠️ Failed to fetch data for {ticker}: {e}")

    print(
        f"📈 Pre-fetched {len(shared_stock_market_data)} stock quotes; sharing across agents"
    )

    # Polymarket can fetch once via its system method
    try:
        shared_polymarket_market_data = polymarket_system._fetch_market_data()
    except Exception as e:
        print(f"⚠️ Failed to pre-fetch polymarket data: {e}")
        shared_polymarket_market_data = {}

    # Function to process a single agent
    def process_single_agent(agent_info):
        try:
            agent_name = agent_info["name"]
            agent = agent_info["agent"]
            system_type = agent_info["system"]
            system_instance = agent_info["system_instance"]

            print(f"🤖 [{system_type.upper()}] {agent_name} starting LLM call...")

            # Get market data based on system type (shared across agents)
            if system_type == "stock":
                market_data = shared_stock_market_data

                # Update position prices with shared data
                for ag in system_instance.agents.values():
                    if hasattr(ag.account, "update_position_price"):
                        for ticker, data in market_data.items():
                            ag.account.update_position_price(
                                ticker, data.get("current_price", 0)
                            )

            else:  # polymarket
                market_data = shared_polymarket_market_data

            if not market_data:
                return {
                    "agent_name": agent_name,
                    "system": system_type,
                    "success": False,
                    "allocation": None,
                }

            # Generate portfolio allocation using the agent
            allocation = agent.generate_portfolio_allocation(market_data)

            if allocation:
                print(
                    f"✅ [{system_type.upper()}] {agent_name} allocation generated successfully"
                )
                return {
                    "agent_name": agent_name,
                    "system": system_type,
                    "success": True,
                    "allocation": allocation,
                }
            else:
                print(
                    f"⚠️ [{system_type.upper()}] {agent_name} no allocation generated"
                )
                return {
                    "agent_name": agent_name,
                    "system": system_type,
                    "success": True,
                    "allocation": None,
                }

        except Exception as e:
            print(f"❌ [{system_type.upper()}] {agent_name} error: {e}")
            import traceback

            traceback.print_exc()
            return {
                "agent_name": agent_name,
                "system": system_type,
                "success": False,
                "error": str(e),
            }

    # Execute all agents in parallel
    results = []
    workers = max(2, min(32, len(all_agents)))
    with ThreadPoolExecutor(max_workers=workers) as executor:
        # Submit all tasks
        future_to_agent = {
            executor.submit(process_single_agent, agent_info): agent_info
            for agent_info in all_agents
        }
        for future in as_completed(future_to_agent):
            agent_info = future_to_agent[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"❌ Task failed for {agent_info['name']}: {e}")
                results.append(
                    {
                        "agent_name": agent_info["name"],
                        "system": agent_info["system"],
                        "success": False,
                        "error": str(e),
                    }
                )

    # Group results by system
    stock_results = [r for r in results if r["system"] == "stock"]
    polymarket_results = [r for r in results if r["system"] == "polymarket"]

    return {
        "success": True,
        "total_agents": len(results),
        "stock_success": len([r for r in stock_results if r["success"]]),
        "polymarket_success": len([r for r in polymarket_results if r["success"]]),
        "results": results,
    }


def trigger_cycle() -> Dict[str, Any]:
    """Run one trading cycle using real live_trade_bench systems with parallel agent processing"""
    try:
        stock_system = _get_stock_system()
        polymarket_system = _get_polymarket_system()

        print("🔄 Triggering parallel LLM trading cycles...")

        # Use parallel agent processing instead of system-level parallelism
        result = _parallel_process_agents(stock_system, polymarket_system)

        if result["success"]:
            print("✅ Parallel LLM trading cycles completed successfully")

            # 🔄 CRITICAL FIX: Save updated data to JSON after parallel processing
            print("💾 Saving updated model data to JSON...")
            try:
                updated_models = get_models_data()
                print(f"✅ Successfully saved {len(updated_models)} models to JSON")
            except Exception as save_error:
                print(f"⚠️ Failed to save models data: {save_error}")
                # Don't fail the whole operation if save fails
                import traceback

                traceback.print_exc()

            return {
                "status": "success",
                "message": "Parallel LLM trading cycles completed successfully",
                "total_agents": result["total_agents"],
                "stock_success": result["stock_success"],
                "polymarket_success": result["polymarket_success"],
                "results": result["results"],
            }
        else:
            return {"status": "error", "message": "Parallel processing failed"}

    except Exception as e:
        print(f"❌ Trading cycle failed: {e}")
        import traceback

        traceback.print_exc()
        return {"status": "error", "message": f"Trading cycle failed: {str(e)}"}


# ============================================================================
# PARALLEL PROCESSING METHODS - 复用现有接口
# ============================================================================


def run_parallel_cycle(stock_system, polymarket_system, for_date=None):
    """并行运行股票和预测市场系统的交易周期"""
    from concurrent.futures import as_completed

    print("🚀 Starting parallel system processing...")

    def run_stock_cycle():
        """运行股票系统周期"""
        try:
            print("📈 Processing stock system...")
            result = stock_system.run_cycle(for_date=for_date)
            print("✅ Stock system completed")
            return {"system": "stock", "result": result}
        except Exception as e:
            print(f"❌ Stock system error: {e}")
            return {"system": "stock", "result": {"success": False, "error": str(e)}}

    def run_polymarket_cycle():
        """运行预测市场系统周期"""
        try:
            print("🎯 Processing polymarket system...")
            result = polymarket_system.run_cycle(for_date=for_date)
            print("✅ Polymarket system completed")
            return {"system": "polymarket", "result": result}
        except Exception as e:
            print(f"❌ Polymarket system error: {e}")
            return {
                "system": "polymarket",
                "result": {"success": False, "error": str(e)},
            }

    # 并行执行两个系统
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            executor.submit(run_stock_cycle): "stock",
            executor.submit(run_polymarket_cycle): "polymarket",
        }

        results = {}
        for future in as_completed(futures):
            result = future.result()
            results[result["system"]] = result["result"]

    # 汇总结果
    stock_success = results.get("stock", {}).get("success", False)
    polymarket_success = results.get("polymarket", {}).get("success", False)

    print("✅ Parallel system processing completed:")
    print(f"   📈 Stock system: {'✅' if stock_success else '❌'}")
    print(f"   🎯 Polymarket system: {'✅' if polymarket_success else '❌'}")

    return {
        "success": stock_success and polymarket_success,
        "stock_result": results.get("stock"),
        "polymarket_result": results.get("polymarket"),
    }


# ============================================================================
# PARALLEL BACKTEST METHODS - 复用现有接口
# ============================================================================


def run_parallel_backtest(
    models, start_date, end_date, stock_initial_cash, polymarket_initial_cash
):
    """并行运行股票和预测市场回测"""
    from concurrent.futures import as_completed

    from live_trade_bench.backtesting import run_backtest

    print("🚀 Starting parallel backtest for both markets...")

    def run_stock_backtest():
        """运行股票市场回测"""
        try:
            print("📈 Running stock market backtest...")
            result = run_backtest(
                models=models,
                initial_cash=stock_initial_cash,
                start_date=start_date,
                end_date=end_date,
                market_type="stock",
            )
            print("✅ Stock backtest completed")
            return {"market": "stock", "result": result}
        except Exception as e:
            print(f"❌ Stock backtest error: {e}")
            return {"market": "stock", "result": {}, "error": str(e)}

    def run_polymarket_backtest():
        """运行预测市场回测"""
        try:
            print("🎯 Running polymarket backtest...")
            result = run_backtest(
                models=models,
                initial_cash=polymarket_initial_cash,
                start_date=start_date,
                end_date=end_date,
                market_type="polymarket",
            )
            print("✅ Polymarket backtest completed")
            return {"market": "polymarket", "result": result}
        except Exception as e:
            print(f"❌ Polymarket backtest error: {e}")
            return {"market": "polymarket", "result": {}, "error": str(e)}

    # 并行执行两个市场的回测
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            executor.submit(run_stock_backtest): "stock",
            executor.submit(run_polymarket_backtest): "polymarket",
        }

        results = {}
        for future in as_completed(futures):
            result = future.result()
            results[result["market"]] = result["result"]

    # 汇总结果
    stock_results = results.get("stock", {})
    polymarket_results = results.get("polymarket", {})

    print("✅ Parallel backtest completed:")
    print(f"   📈 Stock models: {len(stock_results)} results")
    print(f"   🎯 Polymarket models: {len(polymarket_results)} results")

    # 🔄 CRITICAL FIX: Save backtest results to models JSON
    print("💾 Saving backtest results to models JSON...")
    try:
        backtest_data = {"stock": stock_results, "polymarket": polymarket_results}
        _save_backtest_data_to_models(backtest_data)
        print("✅ Backtest data saved to models JSON successfully")
    except Exception as save_error:
        print(f"⚠️ Failed to save backtest data: {save_error}")
        import traceback

        traceback.print_exc()

    return {
        "stock": stock_results,
        "polymarket": polymarket_results,
        "start_date": start_date,
        "end_date": end_date,
    }


if __name__ == "__main__":
    print("🚀 Running models_data generation...")
    models = get_models_data()
    print(f"✅ Generated {len(models)} models successfully!")

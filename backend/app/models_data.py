"""
Real model data provider using live_trade_bench
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from live_trade_bench.agents.polymarket_system import PolymarketPortfolioSystem
from live_trade_bench.agents.stock_system import StockPortfolioSystem


def _get_stock_system():
    """Get or create stock system with real agents"""
    stock_system = StockPortfolioSystem.get_instance()
    if not stock_system.agents:
        # Add real LLM agents
        models = [
            ("GPT-4o", "gpt-4o", 1000),
            ("GPT-4 Turbo", "gpt-4-turbo", 1000),
            ("GPT-4o Mini", "gpt-4o-mini", 1000),
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
            ("GPT-4 Turbo", "gpt-4-turbo", 500),
            ("GPT-4o Mini", "gpt-4o-mini", 500),
        ]

        for name, model_name, initial_cash in models:
            polymarket_system.add_agent(
                name=name, initial_cash=initial_cash, model_name=model_name
            )

    return polymarket_system


def _get_real_market_data_for_system(system) -> Dict[str, Dict[str, Any]]:
    """Get real market data for the system's universe."""
    market_data = {}

    if hasattr(system, "universe") and system.universe:
        # For stock system
        if hasattr(system, "stock_info"):
            from live_trade_bench.fetchers.stock_fetcher import (
                fetch_current_stock_price,
            )

            for ticker in system.universe:
                try:
                    price = fetch_current_stock_price(ticker)
                    if price:
                        market_data[ticker] = {
                            "ticker": ticker,
                            "name": system.stock_info[ticker]["name"],
                            "sector": system.stock_info[ticker]["sector"],
                            "current_price": price,
                            "market_cap": system.stock_info[ticker]["market_cap"],
                        }
                except Exception as e:
                    print(f"⚠️ Failed to fetch data for {ticker}: {e}")

        # For polymarket system
        else:
            from live_trade_bench.fetchers.polymarket_fetcher import (
                fetch_current_market_price,
            )

            for market_id in system.universe:
                try:
                    market_info = fetch_current_market_price(market_id)
                    if market_info:
                        market_data[market_id] = market_info
                except Exception as e:
                    print(f"⚠️ Failed to fetch data for {market_id}: {e}")

    return market_data


async def _generate_real_allocation(agent, system) -> Dict[str, float]:
    """Generate real portfolio allocation using LLM agent."""
    try:
        # Get real market data for the system
        market_data = _get_real_market_data_for_system(system)

        if not market_data:
            print(f"⚠️ No market data available for {agent.name}, using fallback")
            return {"CASH": 1.0}

        # Use the agent's real LLM to generate allocation
        allocation = await agent.generate_portfolio_allocation(
            market_data, agent.account
        )

        if allocation:
            print(f"✅ Generated real allocation for {agent.name}: {allocation}")
            return allocation
        else:
            print(f"⚠️ No allocation generated for {agent.name}, using fallback")
            return {"CASH": 1.0}

    except Exception as e:
        print(f"❌ Error generating real allocation for {agent.name}: {e}")
        # Fallback to safe allocation
        return {"CASH": 1.0}


async def get_models_data() -> List[Dict[str, Any]]:
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

    # 收集所有需要并发处理的 agent 任务
    all_agent_tasks = []
    for category, config in systems.items():
        system = config["system"]
        for agent_name, agent in system.agents.items():
            all_agent_tasks.append((agent_name, agent, category, config))

    # 🚀 并发处理所有 agent！
    async def process_single_agent(
        agent_name: str, agent, category: str, config: Dict
    ) -> Dict[str, Any]:
        """处理单个 agent，返回模型数据"""
        try:
            system = config["system"]
            initial_cash = config["initial_cash"]
            account = agent.account
            model_id = f"{agent_name.lower().replace(' ', '-')}_{category}"

            # 1. Generate real portfolio allocation using LLM agent (并发!)
            real_allocation = await _generate_real_allocation(agent, system)
            account._simulate_rebalance_to_target(real_allocation)
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

            # 4. Generate profit history
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
            else:
                profit_history.append(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "profit": 0.0,
                        "totalValue": initial_cash,
                    }
                )

            # 5. Get chart data
            chart_data = {
                "holdings": portfolio_details["holdings"],
                "profit_history": profit_history,
                "total_value": total_value,
            }

            # 6. Get allocation history
            allocation_history = account.allocation_history

            # 7. Assemble the comprehensive model object
            return {
                "id": model_id,
                "name": agent_name,
                "category": category,
                "performance": round(return_pct, 2),
                "profit": round(profit_amount, 2),
                "trades": len(account.transactions),
                "status": "active",
                "asset_allocation": portfolio_breakdown.get("current_allocations", {}),
                "portfolio": portfolio_details,
                "chartData": chart_data,
                "allocationHistory": allocation_history,
                "last_updated": "2024-01-01T00:00:00Z",
            }
        except Exception as e:
            print(f"❌ Error processing agent {agent_name}: {e}")
            import traceback

            traceback.print_exc()
            return None

    # 执行所有 agent 的并发处理
    print(f"🚀 Processing {len(all_agent_tasks)} agents concurrently...")

    # 创建任务列表
    tasks = [
        process_single_agent(agent_name, agent, category, config)
        for agent_name, agent, category, config in all_agent_tasks
    ]

    # 并发执行所有任务
    import asyncio

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 处理结果
    for result in results:
        if isinstance(result, Exception):
            print(f"❌ Agent processing exception: {result}")
            continue
        if result is not None:
            models.append(result)

    print(f"✅ Processed {len(models)} agents successfully")

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


async def trigger_cycle() -> Dict[str, Any]:
    """Run one trading cycle using real live_trade_bench systems"""
    try:
        stock_system = _get_stock_system()
        polymarket_system = _get_polymarket_system()

        print("🔄 Triggering LLM trading cycles...")

        # Run stock system cycle
        print("  📈 Running stock portfolio cycle...")
        stock_result = await stock_system.run_cycle()

        # Run polymarket system cycle
        print("  🎯 Running polymarket portfolio cycle...")
        poly_result = await polymarket_system.run_cycle()

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

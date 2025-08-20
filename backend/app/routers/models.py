from typing import Any, Dict, List

from app.data import get_real_models_data
from app.schemas import TradingModel
from app.trading_system import get_trading_system
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("/", response_model=list[TradingModel])
async def get_models() -> List[TradingModel]:
    """Get real LLM trading models with performance from actual predictions."""
    try:
        models = get_real_models_data()
        return models
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching models: {str(e)}")


@router.post("/trigger-cycle")
async def trigger_trading_cycle() -> Dict[str, Any]:
    """Manually trigger a trading cycle for all models."""
    try:
        trading_system = get_trading_system()
        trading_system.run_trading_cycle()

        return {
            "success": True,
            "message": "Trading cycle completed",
            "timestamp": trading_system.trading_history[-1]["timestamp"]
            if trading_system.trading_history
            else None,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error running trading cycle: {str(e)}"
        )


@router.get("/system-status")
async def get_system_status() -> Dict[str, Any]:
    """Get multi-asset trading system status and configuration."""
    try:
        trading_system = get_trading_system()

        total_agents = len(trading_system.stock_system.agents) + len(
            trading_system.polymarket_system.agents
        )
        active_agents = len(
            [m for m, active in trading_system.active_stock_models.items() if active]
        ) + len(
            [
                m
                for m, active in trading_system.active_polymarket_models.items()
                if active
            ]
        )

        # Combine both stock and polymarket model activations for frontend compatibility
        combined_active_models = {}
        # Add stock models
        for model_id, active in trading_system.active_stock_models.items():
            combined_active_models[f"{model_id}_stock"] = active
        # Add polymarket models
        for model_id, active in trading_system.active_polymarket_models.items():
            combined_active_models[f"{model_id}_polymarket"] = active

        # Get actual stock tickers from trading system
        actual_stock_tickers = trading_system.get_stock_tickers()

        return {
            "system_running": trading_system.system_running,
            "cycle_interval_minutes": trading_system.cycle_interval // 60,
            "total_agents": total_agents,  # Frontend expects this
            "active_agents": active_agents,  # Frontend expects this
            "tickers": actual_stock_tickers,  # Frontend expects this - now dynamic
            "initial_cash": trading_system.stock_initial_cash,  # Frontend expects this
            # Additional detailed info
            "total_stock_agents": len(trading_system.stock_system.agents),
            "total_polymarket_agents": len(trading_system.polymarket_system.agents),
            "active_stock_agents": len(
                [
                    m
                    for m, active in trading_system.active_stock_models.items()
                    if active
                ]
            ),
            "active_polymarket_agents": len(
                [
                    m
                    for m, active in trading_system.active_polymarket_models.items()
                    if active
                ]
            ),
            "stock_tickers": actual_stock_tickers,  # Now using dynamic tickers
            "stock_initial_cash": trading_system.stock_initial_cash,
            "polymarket_initial_cash": trading_system.polymarket_initial_cash,
            "total_actions": len(trading_system.trading_history),
            "last_cycle_time": trading_system.last_cycle_time.isoformat()
            if trading_system.last_cycle_time
            else None,
            "next_cycle_time": trading_system.next_cycle_time.isoformat()
            if trading_system.next_cycle_time
            else None,
            "execution_stats": trading_system.execution_stats,
            "active_models": combined_active_models,  # Frontend expects this
            "active_stock_models": trading_system.active_stock_models,
            "active_polymarket_models": trading_system.active_polymarket_models,
            "last_action": trading_system.trading_history[-1]
            if trading_system.trading_history
            else None,
            "market_status": trading_system.get_market_status(),  # Market hours info
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting system status: {str(e)}"
        )


@router.post("/cycle-interval")
async def set_cycle_interval(
    minutes: int = Query(
        ..., ge=1, le=1440, description="Cycle interval in minutes (1-1440)"
    )
) -> Dict[str, Any]:
    """Set the trading cycle interval."""
    try:
        trading_system = get_trading_system()

        success = trading_system.set_cycle_interval(minutes)

        if success:
            return {
                "success": True,
                "message": f"Cycle interval set to {minutes} minutes",
                "interval_minutes": minutes,
                "interval_seconds": minutes * 60,
            }
        else:
            raise HTTPException(status_code=400, detail="Invalid interval")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error setting cycle interval: {str(e)}"
        )


@router.get("/execution-logs")
async def get_execution_logs(
    limit: int = Query(
        default=50, ge=1, le=500, description="Number of log entries to return"
    ),
    event_type: str = Query(default=None, description="Filter by event type"),
) -> Dict[str, Any]:
    """Get execution logs from the trading system."""
    try:
        trading_system = get_trading_system()
        logs = trading_system.get_execution_logs(limit=limit, event_type=event_type)

        return {
            "logs": logs,
            "total_logs": len(trading_system.execution_logs),
            "filter_applied": event_type is not None,
            "event_type": event_type,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching execution logs: {str(e)}"
        )


@router.get("/system-metrics")
async def get_system_metrics() -> Dict[str, Any]:
    """Get comprehensive system performance metrics."""
    try:
        trading_system = get_trading_system()
        metrics = trading_system.get_system_metrics()

        return metrics

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching system metrics: {str(e)}"
        )


@router.get("/{model_id}", response_model=TradingModel)
async def get_model(model_id: str) -> TradingModel:
    """Get a specific real trading model by ID."""
    try:
        models = get_real_models_data()
        model = next((m for m in models if m.id == model_id), None)
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
        return model
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching model: {str(e)}")


@router.get("/{model_id}/performance")
async def get_model_performance(model_id: str) -> Dict[str, Any]:
    """Get detailed performance metrics for a specific real model."""
    try:
        models = get_real_models_data()
        model = next((m for m in models if m.id == model_id), None)
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")

        # Return real performance metrics
        return {
            "id": model.id,
            "name": model.name,
            "performance": model.performance,
            "accuracy": model.accuracy,
            "total_trades": model.trades,
            "profit_loss": model.profit,
            "status": model.status.value,
            "win_rate": model.accuracy / 100,
            "average_profit_per_trade": model.profit / model.trades
            if model.trades > 0
            else 0,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching performance: {str(e)}"
        )


@router.post("/{model_id}/activate")
async def activate_model(model_id: str) -> Dict[str, Any]:
    """Activate a trading model (handles both stock and polymarket)."""
    try:
        trading_system = get_trading_system()

        # Extract base model ID and category from full model ID
        base_model_id = model_id.replace("_stock", "").replace("_polymarket", "")

        # Check if the base model exists
        if (
            base_model_id not in trading_system.stock_agents
            and base_model_id not in trading_system.polymarket_agents
        ):
            raise HTTPException(
                status_code=404, detail=f"Model {base_model_id} not found"
            )

        success = trading_system.activate_model(model_id)

        if success:
            return {
                "success": True,
                "message": f"Model {model_id} activated",
                "model_id": model_id,
                "status": "active",
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to activate model")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error activating model: {str(e)}")


@router.post("/{model_id}/deactivate")
async def deactivate_model(model_id: str) -> Dict[str, Any]:
    """Deactivate a trading model (handles both stock and polymarket)."""
    try:
        trading_system = get_trading_system()

        # Extract base model ID from full model ID
        base_model_id = model_id.replace("_stock", "").replace("_polymarket", "")

        # Check if the base model exists
        if (
            base_model_id not in trading_system.stock_agents
            and base_model_id not in trading_system.polymarket_agents
        ):
            raise HTTPException(
                status_code=404, detail=f"Model {base_model_id} not found"
            )

        success = trading_system.deactivate_model(model_id)

        if success:
            return {
                "success": True,
                "message": f"Model {model_id} deactivated",
                "model_id": model_id,
                "status": "inactive",
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to deactivate model")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error deactivating model: {str(e)}"
        )


@router.get("/{model_id}/portfolio")
async def get_model_portfolio(model_id: str) -> Dict[str, Any]:
    """Get portfolio data for a specific model (both stock and polymarket)."""
    try:
        trading_system = get_trading_system()

        # Get portfolio data - the trading system handles model ID validation
        portfolio_data = trading_system.get_portfolio(model_id)

        # Add portfolio history for area chart
        model_actions = [
            action
            for action in trading_system.trading_history
            if action.get("model_id") == model_id
        ]

        # Generate portfolio history snapshots
        portfolio_history = []
        current_holdings = {}
        current_cash = portfolio_data.get("cash", 1000)

        for action in model_actions[-20:]:  # Last 20 actions for history
            if action.get("action") == "BUY":
                ticker = action.get("symbol", "")
                quantity = action.get("quantity", 0)
                if ticker:
                    current_holdings[ticker] = (
                        current_holdings.get(ticker, 0) + quantity
                    )
            elif action.get("action") == "SELL":
                ticker = action.get("symbol", "")
                quantity = action.get("quantity", 0)
                if ticker and ticker in current_holdings:
                    current_holdings[ticker] = max(
                        0, current_holdings[ticker] - quantity
                    )
                    if current_holdings[ticker] == 0:
                        del current_holdings[ticker]

            # Create portfolio snapshot
            prices = {
                ticker: action.get("price", 100) for ticker in current_holdings.keys()
            }
            total_value = current_cash + sum(
                current_holdings.get(ticker, 0) * prices.get(ticker, 100)
                for ticker in current_holdings.keys()
            )

            portfolio_history.append(
                {
                    "timestamp": action.get("timestamp", ""),
                    "holdings": current_holdings.copy(),
                    "prices": prices,
                    "cash": current_cash,
                    "totalValue": total_value,
                }
            )

        # Add current state if no history
        if not portfolio_history:
            portfolio_history = [
                {
                    "timestamp": "2024-01-01T00:00:00Z",
                    "holdings": portfolio_data.get("holdings", {}),
                    "prices": {
                        ticker: 100
                        for ticker in portfolio_data.get("holdings", {}).keys()
                    },
                    "cash": current_cash,
                    "totalValue": portfolio_data.get("total_value", 1000),
                }
            ]

        portfolio_data["portfolio_history"] = portfolio_history

        return portfolio_data

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching portfolio: {str(e)}"
        )


@router.get("/{model_id}/chart-data")
async def get_model_chart_data(model_id: str) -> Dict[str, Any]:
    """Get chart data (holdings allocation and profit history) for a specific model."""
    try:
        trading_system = get_trading_system()

        # Get current portfolio for holdings allocation
        portfolio_data = trading_system.get_portfolio(model_id)
        holdings = portfolio_data.get("holdings", {})

        # Get profit history from trading history
        profit_history = []
        model_actions = [
            action
            for action in trading_system.trading_history
            if action.get("model_id") == model_id
        ]

        # Calculate cumulative profit over time
        cumulative_profit = 0
        total_value = portfolio_data.get("total_value", 1000)  # Start with initial cash

        for i, action in enumerate(model_actions[-30:]):  # Last 30 actions for chart
            if action.get("action") == "BUY":
                # Buying reduces profit temporarily (cash to holdings)
                pass
            elif action.get("action") == "SELL":
                # Selling realizes profit/loss
                price = action.get("price", 0)
                quantity = action.get("quantity", 0)
                cumulative_profit += (price * quantity) - action.get(
                    "cost_basis", price * quantity
                )

            profit_history.append(
                {
                    "timestamp": action.get("timestamp", ""),
                    "profit": cumulative_profit,
                    "totalValue": total_value + cumulative_profit,
                }
            )

        # If no history, create a single point
        if not profit_history:
            profit_history = [
                {
                    "timestamp": "2024-01-01T00:00:00Z",
                    "profit": 0,
                    "totalValue": total_value,
                }
            ]

        return {
            "holdings": holdings,
            "profit_history": profit_history,
            "total_value": total_value,
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching chart data: {str(e)}"
        )

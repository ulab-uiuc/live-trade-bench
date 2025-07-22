from datetime import datetime, timedelta

from app.data import get_real_system_log_data
from app.schemas import ActionStatus, ActionType, Portfolio, SystemLogStats
from app.trading_actions import (
    MODEL_PORTFOLIOS,
    add_trading_action,
    get_model_portfolio,
    update_action_status,
)
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/system-log", tags=["system-logs"])


@router.get("/")
async def get_system_log(
    agent_type: str = Query(
        default=None,
        description="Filter by agent type (data_collector, trading_agent, etc.)",
    ),
    status: str = Query(
        default=None, description="Filter by status (success, warning, error, info)"
    ),
    limit: int = Query(default=100, ge=1, le=500),
    hours: int = Query(
        default=24, ge=1, le=168, description="Number of hours to look back"
    ),
):
    """Get real system log data from trading operations."""
    try:
        actions = get_real_system_log_data(
            agent_type=agent_type, status=status, limit=limit, hours=hours
        )
        return actions
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching system log: {str(e)}"
        )


@router.get("/stats", response_model=SystemLogStats)
async def get_system_log_stats():
    """Get system log statistics for trading actions."""
    try:
        actions = get_real_system_log_data(limit=1000, hours=24)

        if not actions:
            return SystemLogStats(
                total_actions=0,
                pending_actions=0,
                executed_actions=0,
                evaluated_actions=0,
                models_active=0,
                recent_activity=0,
            )

        # Calculate statistics
        total_actions = len(actions)
        pending_actions = len([a for a in actions if a["status"] == "pending"])
        executed_actions = len([a for a in actions if a["status"] == "executed"])
        evaluated_actions = len([a for a in actions if a["status"] == "evaluated"])

        # Count active models (models with actions in last 24 hours)
        active_models = len(set(a["agent_id"] for a in actions))

        # Recent activity (last hour)
        one_hour_ago = datetime.now() - timedelta(hours=1)
        recent_activity = len(
            [
                a
                for a in actions
                if datetime.fromisoformat(a["timestamp"].replace("Z", "+00:00"))
                >= one_hour_ago
            ]
        )

        return SystemLogStats(
            total_actions=total_actions,
            pending_actions=pending_actions,
            executed_actions=executed_actions,
            evaluated_actions=evaluated_actions,
            models_active=active_models,
            recent_activity=recent_activity,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error calculating stats: {str(e)}"
        )


@router.get("/portfolios")
async def get_all_portfolios():
    """Get portfolios for all trading models."""
    try:
        portfolios = {}
        for model_id, portfolio in MODEL_PORTFOLIOS.items():
            portfolios[model_id] = {
                "model_id": model_id,
                "model_name": _get_model_name(model_id),
                "cash": portfolio.cash,
                "holdings": dict(portfolio.holdings),
                "total_value": portfolio.cash
                + sum(
                    quantity * 150.0  # Simplified price for demo
                    for quantity in portfolio.holdings.values()
                ),
            }
        return portfolios
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching portfolios: {str(e)}"
        )


@router.get("/portfolios/{model_id}", response_model=Portfolio)
async def get_portfolio(model_id: str):
    """Get portfolio for a specific trading model."""
    try:
        portfolio = get_model_portfolio(model_id)
        return portfolio
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching portfolio: {str(e)}"
        )


@router.post("/actions")
async def create_trading_action(
    model_id: str = Query(..., description="Model ID (e.g., claude-3.5-sonnet)"),
    action_type: ActionType = Query(..., description="Action type: BUY, SELL, or HOLD"),
    ticker: str = Query(..., description="Stock ticker symbol"),
    quantity: float = Query(..., description="Number of shares"),
    price: float = Query(..., description="Price per share"),
    reasoning: str = Query(default="", description="Reasoning for the action"),
):
    """Create a new trading action for a model."""
    try:
        action_id = add_trading_action(
            model_id=model_id,
            action_type=action_type,
            ticker=ticker,
            quantity=quantity,
            price=price,
            reasoning=reasoning,
        )
        return {
            "success": True,
            "action_id": action_id,
            "message": "Trading action created successfully",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating action: {str(e)}")


@router.put("/actions/{action_id}/status")
async def update_trading_action_status(
    action_id: str,
    status: ActionStatus = Query(..., description="New status for the action"),
):
    """Update the status of a trading action."""
    try:
        success = update_action_status(action_id, status)
        if not success:
            raise HTTPException(status_code=404, detail="Action not found")

        return {"success": True, "message": f"Action status updated to {status.value}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating action: {str(e)}")


def _get_model_name(model_id: str) -> str:
    """Get human readable model name."""
    name_mapping = {
        "claude-3.5-sonnet": "Claude 3.5 Sonnet",
        "gpt-4": "GPT-4",
        "gemini-1.5-pro": "Gemini 1.5 Pro",
        "claude-4-haiku": "Claude 4 Haiku",
    }
    return name_mapping.get(model_id, model_id)

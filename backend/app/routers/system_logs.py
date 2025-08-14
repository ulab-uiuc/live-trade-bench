from app.schemas import Portfolio, SystemLogStats
from app.trading_system import get_trading_system
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/system-log", tags=["system-logs"])


@router.get("/")
async def get_system_log(
    agent_type: str = Query(
        default=None,
        description="Filter by agent type (data_collector, trading_agent, etc.)",
    ),
    status: str = Query(
        default=None, description="Filter by status (executed, failed, pending)"
    ),
    limit: int = Query(default=100, ge=1, le=500),
    hours: int = Query(
        default=24, ge=1, le=168, description="Number of hours to look back"
    ),
):
    """Get real system log data from trading operations."""
    try:
        trading_system = get_trading_system()

        # Get recent actions from trading system
        actions = trading_system.get_recent_actions(hours=hours)

        # Apply filters
        if agent_type and agent_type != "trading_agent":
            # Only trading_agent type is available
            actions = []

        if status:
            actions = [a for a in actions if a.get("status") == status]

        # Limit results
        actions = actions[:limit]

        return actions

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching system log: {str(e)}"
        )


@router.get("/stats", response_model=SystemLogStats)
async def get_system_log_stats():
    """Get system log statistics for trading actions."""
    try:
        trading_system = get_trading_system()
        actions = trading_system.get_recent_actions(hours=24)

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
        pending_actions = len([a for a in actions if a.get("status") == "pending"])
        executed_actions = len([a for a in actions if a.get("status") == "executed"])
        evaluated_actions = len([a for a in actions if a.get("status") == "evaluated"])

        # Count active models (models with actions in last 24 hours)
        active_models = len(set(a["agent_id"] for a in actions))

        # Recent activity (last hour)
        recent_actions = trading_system.get_recent_actions(hours=1)
        recent_activity = len(recent_actions)

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
        trading_system = get_trading_system()
        portfolios = {}

        # Get portfolios from trading system
        for model_id in trading_system.agents.keys():
            try:
                portfolio_data = trading_system.get_portfolio(model_id)
                portfolios[model_id] = portfolio_data
            except Exception as e:
                print(f"Error getting portfolio for {model_id}: {e}")
                # Don't add fallback data - just skip this portfolio
                continue

        return portfolios
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching portfolios: {str(e)}"
        )


@router.get("/portfolios/{model_id}")
async def get_portfolio(model_id: str):
    """Get portfolio for a specific trading model."""
    try:
        trading_system = get_trading_system()

        if model_id not in trading_system.agents:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")

        portfolio_data = trading_system.get_portfolio(model_id)

        # Convert to Portfolio schema format
        portfolio = Portfolio(
            cash=portfolio_data["cash"], holdings=portfolio_data["holdings"]
        )

        return portfolio

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching portfolio: {str(e)}"
        )


def _get_model_name(model_id: str) -> str:
    """Get human readable model name."""
    name_mapping = {
        "claude-3.5-sonnet": "Claude 3.5 Sonnet",
        "gpt-4": "GPT-4",
        "gemini-1.5-pro": "Gemini 1.5 Pro",
        "claude-4-haiku": "Claude 4 Haiku",
    }
    return name_mapping.get(model_id, model_id)

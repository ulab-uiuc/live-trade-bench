import logging
from typing import Any, Dict, List

from app.models_data import get_models_data, get_system_status, trigger_cycle
from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("/")
async def get_models() -> List[Dict[str, Any]]:
    """Get real LLM trading models with performance from actual predictions."""
    try:
        models = await get_models_data()
        return models
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching models: {str(e)}")


@router.post("/trigger-cycle")
async def trigger_trading_cycle() -> Dict[str, Any]:
    """Manually trigger a trading cycle for all models."""
    try:
        result = await trigger_cycle()
        if result["status"] == "success":
            return {
                "success": True,
                "message": result["message"],
                "timestamp": None,
            }
        else:
            raise HTTPException(status_code=500, detail=result["message"])
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error running trading cycle: {str(e)}"
        )


@router.get("/system-status")
async def system_status() -> Dict[str, Any]:
    """Get multi-asset trading system status and configuration."""
    try:
        status = get_system_status()
        return {
            "running": status["running"],
            "total_agents": status["total_agents"],
            "stock_agents": status["stock_agents"],
            "polymarket_agents": status["polymarket_agents"],
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting system status: {str(e)}"
        )

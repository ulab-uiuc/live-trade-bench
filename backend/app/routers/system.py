from typing import Any, Dict

from app.system_data import get_system_status
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/status")
async def system_status() -> Dict[str, Any]:
    """Get system status from JSON file."""
    try:
        status = get_system_status()
        return {
            "running": status["running"],
            "total_agents": status["total_agents"],
            "stock_agents": status["stock_agents"],
            "polymarket_agents": status["polymarket_agents"],
            "last_updated": status["last_updated"],
            "uptime": status["uptime"],
            "version": status["version"],
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting system status: {str(e)}"
        )

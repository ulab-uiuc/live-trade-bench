from typing import Any, Dict

from app.config import SYSTEM_DATA_FILE
from app.routers.router_utils import read_json_or_404
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/status")
async def system_status() -> Dict[str, Any]:
    try:
        status = read_json_or_404(SYSTEM_DATA_FILE)
        return {
            "running": status.get("running", True),
            "total_agents": status.get("total_agents", 0),
            "stock_agents": status.get("stock_agents", 0),
            "polymarket_agents": status.get("polymarket_agents", 0),
            "last_updated": status.get("last_updated"),
            "uptime": status.get("uptime", "Active"),
            "version": status.get("version", "1.0.0"),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting system status: {e}")

from typing import Any, Dict
import json
import os
from fastapi import APIRouter, HTTPException
from app.config import SYSTEM_DATA_FILE

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/status")
async def system_status() -> Dict[str, Any]:
    """Get system status from JSON file."""
    try:
        if not os.path.exists(SYSTEM_DATA_FILE):
            raise HTTPException(status_code=404, detail="System status not ready yet.")

        with open(SYSTEM_DATA_FILE, "r") as f:
            status = json.load(f)

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
        raise HTTPException(status_code=500, detail=f"Error getting system status: {str(e)}")

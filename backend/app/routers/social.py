import json
import os
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/social", tags=["social"])


@router.get("/stock")
async def get_stock_social(limit: int = 15) -> List[Dict[str, Any]]:
    """Get stock social media data from JSON file."""
    try:
        if not os.path.exists("social_data.json"):
            raise HTTPException(status_code=404, detail="Social data not ready yet.")

        with open("social_data.json", "r") as f:
            social_data = json.load(f)

        return social_data.get("stock", [])

    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Error reading social data file.")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching stock social data: {str(e)}"
        )


@router.get("/polymarket")
async def get_polymarket_social(limit: int = 15) -> List[Dict[str, Any]]:
    """Get polymarket social media data from JSON file."""
    try:
        if not os.path.exists("social_data.json"):
            raise HTTPException(status_code=404, detail="Social data not ready yet.")

        with open("social_data.json", "r") as f:
            social_data = json.load(f)

        return social_data.get("polymarket", [])

    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Error reading social data file.")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching polymarket social data: {str(e)}"
        )

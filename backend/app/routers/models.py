import json
import logging
import os
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("/")
async def get_models() -> List[Dict[str, Any]]:
    """Get models data from JSON file written by background task."""
    try:
        if not os.path.exists("models_data.json"):
            raise HTTPException(
                status_code=404,
                detail="Model data not ready yet. Please wait for background task.",
            )

        with open("models_data.json", "r") as f:
            models = json.load(f)

        return models

    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Error reading model data file.")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Model data file not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching models: {str(e)}")

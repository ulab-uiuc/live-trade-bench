import json
import logging
import os
from typing import Any, Dict, List

# 使用统一配置管理
from app.config import MODELS_DATA_FILE
from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("/")
def get_models() -> List[Dict[str, Any]]:
    """Get models data from JSON file written by background task."""
    try:
        if not os.path.exists(MODELS_DATA_FILE):
            raise HTTPException(
                status_code=404,
                detail="Model data not ready yet. Please wait for background task.",
            )

        with open(MODELS_DATA_FILE, "r") as f:
            models = json.load(f)

        return models

    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Error reading model data file.")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Model data file not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching models: {str(e)}")

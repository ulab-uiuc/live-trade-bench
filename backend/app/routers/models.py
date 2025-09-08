import json
import logging
import os
from typing import Any, Dict, List

# 使用统一配置管理
from app.config import MODELS_DATA_FILE
from app.routers.router_utils import read_json_or_404, slice_limit
from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("/")
def get_models(limit: int = 1000) -> List[Dict[str, Any]]:
    try:
        data = read_json_or_404(MODELS_DATA_FILE)
        return slice_limit(data, limit, 1000, 5000)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching models: {e}")

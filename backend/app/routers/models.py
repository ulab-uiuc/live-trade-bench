import logging
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException
from backend.app.config import MODELS_DATA_FILE
from backend.app.router_utils import read_json_file

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/models", response_model=List[Dict[str, Any]])
def get_models():
    return read_json_file(MODELS_DATA_FILE, "Models data not found.")

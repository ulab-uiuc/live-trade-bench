import logging
from typing import Any, Dict, List

from fastapi import APIRouter

from ..config import MODELS_DATA_FILE
from .router_utils import read_json_or_404

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/models", response_model=List[Dict[str, Any]])
def get_models():
    return read_json_or_404(MODELS_DATA_FILE)

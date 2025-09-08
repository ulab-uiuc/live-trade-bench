from typing import Any, Dict
from fastapi import APIRouter
from ..config import SYSTEM_DATA_FILE
from .router_utils import read_json_or_404

router = APIRouter()

@router.get("/system", response_model=Dict[str, Any])
def get_system_status():
    return read_json_or_404(SYSTEM_DATA_FILE)

from typing import Any, Dict
from fastapi import APIRouter
from backend.app.config import SYSTEM_DATA_FILE
from backend.app.router_utils import read_json_file

router = APIRouter()

@router.get("/system", response_model=Dict[str, Any])
def get_system_status():
    return read_json_file(SYSTEM_DATA_FILE, "System data not found.")

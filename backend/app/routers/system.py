from typing import Any, Dict

from fastapi import APIRouter

from ..config import SYSTEM_DATA_FILE
from ..counter_data import get_visit_count, increment_visit_count
from .router_utils import read_json_or_404

router = APIRouter()


@router.get("/system", response_model=Dict[str, Any], include_in_schema=False)
@router.get("/system/", response_model=Dict[str, Any])
def get_system_status():
    return read_json_or_404(SYSTEM_DATA_FILE)


@router.get("/views")
def get_views():
    return {"views": get_visit_count()}


@router.post("/views")
def increment_views():
    return {"views": increment_visit_count()}

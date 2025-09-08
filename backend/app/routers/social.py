from typing import Any, Dict, List
from fastapi import APIRouter
from backend.app.config import SOCIAL_DATA_FILE
from backend.app.router_utils import read_json_file, get_paginated_data

router = APIRouter()

@router.get("/social", response_model=Dict[str, List[Dict[str, Any]]])
def get_social_media(limit: int = 10, page: int = 1):
    data = read_json_file(SOCIAL_DATA_FILE, "Social media data not found.")
    return get_paginated_data(data, limit, page)

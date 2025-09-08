from typing import Any, Dict, List
from fastapi import APIRouter
from backend.app.config import NEWS_DATA_FILE
from backend.app.router_utils import read_json_file, get_paginated_data

router = APIRouter()

@router.get("/news", response_model=Dict[str, List[Dict[str, Any]]])
def get_news(limit: int = 10, page: int = 1):
    data = read_json_file(NEWS_DATA_FILE, "News data not found.")
    return get_paginated_data(data, limit, page)

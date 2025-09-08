import json
import os
from typing import Any, Dict, List, Sequence, TypeVar

from fastapi import HTTPException

T = TypeVar("T")


def read_json_or_404(file_path: str) -> Dict[str, Any]:
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Data not ready yet.")
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Error reading data file.")


def slice_limit(items: Sequence[T], limit: int, default_limit: int, max_limit: int) -> List[T]:
    lim = default_limit if limit is None else limit
    lim = max(1, min(lim, max_limit))
    return list(items[:lim])



from __future__ import annotations

from typing import Any, Dict, Optional


def normalize_allocations(parsed: Dict[str, Any]) -> Optional[Dict[str, float]]:
    allocations = parsed.get("allocations", {}) if isinstance(parsed, dict) else {}
    if not isinstance(allocations, dict) or not allocations:
        return None

    cleaned: Dict[str, float] = {}
    for key, value in allocations.items():
        if isinstance(value, (int, float)):
            weight = float(value)
            if weight < 0:
                weight = 0.0
            cleaned[key] = min(1.0, weight)

    if "CASH" not in cleaned:
        non_cash_sum = sum(v for k, v in cleaned.items() if k != "CASH")
        cleaned["CASH"] = max(0.0, 1.0 - non_cash_sum)

    total = sum(cleaned.values())
    if total <= 0:
        return {"CASH": 1.0}

    normalized = {k: (v / total) for k, v in cleaned.items()}

    non_cash_sum = sum(v for k, v in normalized.items() if k != "CASH")
    normalized["CASH"] = max(0.0, 1.0 - non_cash_sum)

    return normalized


def parse_llm_response_to_json(content: str) -> Optional[Dict[str, Any]]:
    import json

    try:
        if "```json" in content:
            json_str = content.split("```json")[1].split("```")[0].strip()
        else:
            content = content.strip()
            start = content.find("{")
            end = content.rfind("}") + 1
            if start == -1 or end == 0:
                return None
            json_str = content[start:end]
        return json.loads(json_str)
    except (json.JSONDecodeError, IndexError):
        return None

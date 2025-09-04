import random
from datetime import datetime, timedelta
from typing import Any, Dict, List

from fastapi import APIRouter

router = APIRouter(prefix="/api/polymarket", tags=["polymarket"])


@router.get("/")
async def get_polymarket_data() -> List[Dict[str, Any]]:
    """Get mock polymarket data."""

    markets = []
    topics = [
        "2024 Presidential Election",
        "AI Breakthrough by 2025",
        "Fed Rate Cut in Q1",
        "Climate Action Bill",
        "Crypto ETF Approval",
    ]

    for i, topic in enumerate(topics):
        markets.append(
            {
                "id": f"market_{i}",
                "question": topic,
                "current_price": round(random.uniform(0.3, 0.8), 2),
                "volume": random.randint(10000, 100000),
                "end_date": (
                    datetime.now() + timedelta(days=random.randint(30, 365))
                ).isoformat(),
                "category": "politics" if "Election" in topic else "technology",
                "active": True,
            }
        )

    return markets

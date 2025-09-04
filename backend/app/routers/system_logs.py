from typing import Any, Dict, List
from fastapi import APIRouter
from datetime import datetime, timedelta
import random

router = APIRouter(prefix="/api/system-logs", tags=["system-logs"])

@router.get("/")
async def get_system_logs() -> List[Dict[str, Any]]:
    """Get mock system logs."""
    
    logs = []
    for i in range(10):
        logs.append({
            "id": f"log_{i}",
            "timestamp": (datetime.now() - timedelta(minutes=random.randint(1, 60))).isoformat(),
            "level": random.choice(["INFO", "WARNING", "ERROR"]),
            "message": f"Trading cycle completed for model {random.choice(['GPT-4o', 'Claude 3.5 Sonnet'])}",
            "source": "trading_system"
        })
    
    return logs

@router.get("/stats")
async def get_log_stats() -> Dict[str, Any]:
    """Get system log statistics."""
    return {
        "total_logs": 150,
        "errors": 5,
        "warnings": 12,
        "info": 133,
        "last_24h": 45
    }
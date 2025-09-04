from typing import Any, Dict, List
from fastapi import APIRouter
import random
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/trades", tags=["trades"])

@router.get("/")
async def get_trades() -> List[Dict[str, Any]]:
    """Get mock trading data."""
    
    # Generate some mock trades
    trades = []
    companies = ["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA", "META", "AMZN"]
    models = ["GPT-4o", "Claude 3.5 Sonnet", "GPT-4 Turbo"]
    
    for i in range(15):
        company = random.choice(companies)
        model = random.choice(models)
        action = random.choice(["buy", "sell"])
        
        trades.append({
            "id": f"trade_{i}",
            "model_name": model,
            "symbol": company,
            "action": action,
            "quantity": random.randint(1, 100),
            "price": round(random.uniform(100, 300), 2),
            "timestamp": (datetime.now() - timedelta(hours=random.randint(1, 48))).isoformat(),
            "status": "executed",
            "profit_loss": round(random.uniform(-50, 100), 2)
        })
    
    return trades
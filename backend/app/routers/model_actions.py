from typing import Any, Dict, List
from fastapi import APIRouter
import random
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/model-actions", tags=["model-actions"])

@router.get("/")
async def get_model_actions() -> List[Dict[str, Any]]:
    """Get mock model actions/trades."""
    
    actions = []
    models = ["GPT-4o", "Claude 3.5 Sonnet", "GPT-4 Turbo"]
    symbols = ["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA"]
    
    for i in range(20):
        model = random.choice(models)
        symbol = random.choice(symbols)
        action_type = random.choice(["BUY", "SELL", "REBALANCE"])
        
        actions.append({
            "id": f"action_{i}",
            "model_id": f"{model.lower().replace(' ', '-')}_stock",
            "model_name": model,
            "symbol": symbol,
            "action_type": action_type,
            "quantity": random.randint(1, 50),
            "price": round(random.uniform(100, 300), 2),
            "timestamp": (datetime.now() - timedelta(hours=random.randint(1, 48))).isoformat(),
            "status": "executed",
            "reasoning": f"Model decided to {action_type.lower()} {symbol} based on market analysis"
        })
    
    return actions
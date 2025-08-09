from app.data import get_real_models_data
from app.schemas import TradingModel
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("/", response_model=list[TradingModel])
async def get_models():
    """Get real LLM trading models with performance from actual predictions."""
    try:
        models = get_real_models_data()
        return models
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching models: {str(e)}")


@router.get("/{model_id}", response_model=TradingModel)
async def get_model(model_id: str):
    """Get a specific real trading model by ID."""
    try:
        models = get_real_models_data()
        model = next((m for m in models if m.id == model_id), None)
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
        return model
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching model: {str(e)}")


@router.get("/{model_id}/performance")
async def get_model_performance(model_id: str):
    """Get detailed performance metrics for a specific real model."""
    try:
        models = get_real_models_data()
        model = next((m for m in models if m.id == model_id), None)
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")

        # Return real performance metrics
        return {
            "id": model.id,
            "name": model.name,
            "performance": model.performance,
            "accuracy": model.accuracy,
            "total_trades": model.trades,
            "profit_loss": model.profit,
            "status": model.status.value,
            "win_rate": model.accuracy / 100,
            "average_profit_per_trade": model.profit / model.trades
            if model.trades > 0
            else 0,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching performance: {str(e)}"
        )

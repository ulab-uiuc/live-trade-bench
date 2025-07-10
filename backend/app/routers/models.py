from app.data import SAMPLE_MODELS, get_models_data
from app.schemas import APIResponse, TradingModel
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix='/api/models', tags=['models'])


@router.get('/', response_model=list[TradingModel])
async def get_models():
    """Get all trading models with current performance metrics."""
    try:
        models = get_models_data()
        return models
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error fetching models: {str(e)}')


@router.get('/real', response_model=list[TradingModel])
async def get_real_models():
    """Get real LLM trading models with performance from actual predictions."""
    try:
        models = get_real_models_data()
        return models
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error fetching real models: {str(e)}')


@router.get('/{model_id}', response_model=TradingModel)
async def get_model(model_id: str):
    """Get a specific trading model by ID."""
    try:
        models = get_models_data()
        model = next((m for m in models if m.id == model_id), None)
        if not model:
            raise HTTPException(status_code=404, detail='Model not found')
        return model
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error fetching model: {str(e)}')


@router.post('/{model_id}/toggle', response_model=APIResponse)
async def toggle_model(model_id: str):
    """Toggle a trading model's status (active/inactive)."""
    try:
        model = next((m for m in SAMPLE_MODELS if m.id == model_id), None)
        if not model:
            raise HTTPException(status_code=404, detail='Model not found')

        # Toggle between active and inactive
        if model.status.value == 'active':
            model.status = 'inactive'
        elif model.status.value == 'inactive':
            model.status = 'active'

        return APIResponse(
            success=True,
            message=f'Model {model.name} is now {model.status.value}',
            data={'id': model_id, 'status': model.status.value},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error toggling model: {str(e)}')


@router.get('/{model_id}/performance')
async def get_model_performance(model_id: str):
    """Get detailed performance metrics for a specific model."""
    try:
        model = next((m for m in SAMPLE_MODELS if m.id == model_id), None)
        if not model:
            raise HTTPException(status_code=404, detail='Model not found')

        # Return detailed performance metrics
        return {
            'id': model.id,
            'name': model.name,
            'performance': model.performance,
            'accuracy': model.accuracy,
            'total_trades': model.trades,
            'profit_loss': model.profit,
            'status': model.status.value,
            'win_rate': model.accuracy / 100,
            'average_profit_per_trade': model.profit / model.trades
            if model.trades > 0
            else 0,
            'risk_metrics': {
                'sharpe_ratio': round(
                    model.performance / 15, 2
                ),  # Simplified calculation
                'max_drawdown': round(model.profit * 0.1, 2),  # Simplified calculation
                'volatility': round(
                    model.performance * 0.2, 2
                ),  # Simplified calculation
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f'Error fetching performance: {str(e)}'
        )

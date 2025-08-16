"""
Model Actions Router - Provides real trading actions from AI agents
"""

import logging
from typing import Any, Dict, List

from app.trading_system import get_trading_system
from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/model-actions", tags=["model-actions"])


@router.get("/")
async def get_model_actions(
    model_id: str = Query(default=None, description="Filter by specific model ID"),
    limit: int = Query(
        default=50, ge=1, le=500, description="Number of actions to return"
    ),
    hours: int = Query(
        default=24, ge=1, le=168, description="Hours of history to include"
    ),
) -> List[Dict[str, Any]]:
    """Get recent trading actions from AI agents"""
    try:
        trading_system = get_trading_system()

        # Check if trading system is properly initialized
        if (
            not trading_system.stock_system.agents
            and not trading_system.polymarket_system.agents
        ):
            raise HTTPException(
                status_code=503,
                detail="Trading system not initialized - no agents available",
            )

        # Get recent actions from trading system
        actions = trading_system.get_recent_actions(model_id=model_id, hours=hours)

        # If no actions, return empty list instead of error
        # This is normal when the system is just starting or no significant price changes occurred
        if not actions:
            return []

        # Limit results
        actions = actions[:limit]

        # Transform to frontend format
        model_actions = []
        for action in actions:
            try:
                metadata = action.get("metadata", {})

                # Map to frontend ModelAction format
                model_action = {
                    "id": action["id"],
                    "modelId": action["agent_id"],
                    "modelName": action["agent_name"],
                    "action": action["action"].lower(),  # BUY -> buy
                    "symbol": metadata.get("ticker", "UNKNOWN"),
                    "price": metadata.get("price", 0.0),
                    "quantity": metadata.get("quantity", 0),
                    "confidence": 0.75,  # Default confidence
                    "reason": action["description"],
                    "timestamp": action["timestamp"],
                    "category": "stock",  # All are stock actions for now
                    "status": "executed"
                    if action["status"] == "executed"
                    else "failed",
                }

                model_actions.append(model_action)

            except Exception:
                # Skip malformed actions
                continue

        return model_actions

    except Exception as e:
        logger.error(f"Error in get_model_actions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error fetching model actions: {str(e)}"
        )


@router.get("/stats")
async def get_model_actions_stats(
    hours: int = Query(
        default=24, ge=1, le=168, description="Hours of history to analyze"
    )
) -> Dict[str, Any]:
    """Get statistics about model actions"""
    try:
        trading_system = get_trading_system()

        # Get all recent actions
        actions = trading_system.get_recent_actions(hours=hours)

        # Calculate statistics
        total_actions = len(actions)
        buy_actions = len([a for a in actions if a["action"] == "BUY"])
        sell_actions = len([a for a in actions if a["action"] == "SELL"])
        hold_actions = total_actions - buy_actions - sell_actions

        executed_actions = len([a for a in actions if a["status"] == "executed"])
        failed_actions = len([a for a in actions if a["status"] == "failed"])

        # Active models (models that took actions)
        active_models = len(set(a["agent_id"] for a in actions))

        # Recent activity (last hour)
        recent_actions = trading_system.get_recent_actions(hours=1)
        recent_activity = len(recent_actions)

        return {
            "total_actions": total_actions,
            "buy_actions": buy_actions,
            "sell_actions": sell_actions,
            "hold_actions": hold_actions,
            "executed_actions": executed_actions,
            "failed_actions": failed_actions,
            "active_models": active_models,
            "recent_activity": recent_activity,
            "success_rate": (executed_actions / max(total_actions, 1)) * 100,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error calculating stats: {str(e)}"
        )


@router.get("/{model_id}")
async def get_model_specific_actions(
    model_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    hours: int = Query(default=24, ge=1, le=168),
) -> Dict[str, Any]:
    """Get actions for a specific model"""
    try:
        trading_system = get_trading_system()

        # Check if model exists in either stock or polymarket systems
        base_model_id = model_id.replace("_stock", "").replace("_polymarket", "")
        stock_agents = trading_system.stock_system.agents
        polymarket_agents = trading_system.polymarket_system.agents

        model_found = (
            model_id.endswith("_stock")
            and any(base_model_id in name for name in stock_agents.keys())
            or model_id.endswith("_polymarket")
            and any(base_model_id in name for name in polymarket_agents.keys())
            or any(
                base_model_id in name
                for name in list(stock_agents.keys()) + list(polymarket_agents.keys())
            )
        )

        if not model_found:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")

        # Get actions for this model
        actions = trading_system.get_recent_actions(model_id=model_id, hours=hours)
        actions = actions[:limit]

        # Transform to frontend format
        model_actions = []
        for action in actions:
            metadata = action.get("metadata", {})

            model_action = {
                "id": action["id"],
                "modelId": action["agent_id"],
                "modelName": action["agent_name"],
                "action": action["action"].lower(),
                "symbol": metadata.get("ticker", "UNKNOWN"),
                "price": metadata.get("price", 0.0),
                "quantity": metadata.get("quantity", 0),
                "confidence": 0.75,
                "reason": action["description"],
                "timestamp": action["timestamp"],
                "category": "stock",
                "status": "executed" if action["status"] == "executed" else "failed",
            }

            model_actions.append(model_action)

        # Get model performance summary
        model_data = trading_system.get_model_data()
        model_info = next((m for m in model_data if m["id"] == model_id), None)

        return {
            "model_id": model_id,
            "model_info": model_info,
            "actions": model_actions,
            "total_actions": len(actions),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching model actions: {str(e)}"
        )

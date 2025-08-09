"""
Trading actions management for system logs.
Handles portfolio tracking and action logging for trading models.
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List

from app.schemas import ActionStatus, ActionType, Portfolio

# In-memory storage for model portfolios and trading actions
# In production, this would be a database
MODEL_PORTFOLIOS: Dict[str, Portfolio] = {
    "claude-3.5-sonnet": Portfolio(cash=100.0, holdings={}),
    "gpt-4": Portfolio(cash=100.0, holdings={}),
    "gemini-1.5-pro": Portfolio(cash=100.0, holdings={}),
    "claude-4-haiku": Portfolio(cash=100.0, holdings={}),
}

# Trading actions storage - list of TradingAction dicts
TRADING_ACTIONS: List[Dict] = []


def add_trading_action(
    model_id: str,
    action_type: ActionType,
    ticker: str,
    quantity: float,
    price: float,
    reasoning: str = "",
) -> str:
    """Add a trading action to system logs when a model makes a decision."""

    # Get current portfolio
    portfolio_before = MODEL_PORTFOLIOS.get(
        model_id, Portfolio(cash=100.0, holdings={})
    )

    # Create action
    action_id = str(uuid.uuid4())[:8]

    # Calculate portfolio changes
    portfolio_after = Portfolio(
        cash=portfolio_before.cash, holdings=portfolio_before.holdings.copy()
    )

    total_cost = quantity * price

    if action_type == ActionType.BUY:
        if portfolio_after.cash >= total_cost:
            portfolio_after.cash -= total_cost
            portfolio_after.holdings[ticker] = (
                portfolio_after.holdings.get(ticker, 0) + quantity
            )
            description = f"BUY {quantity} shares of {ticker} at ${price:.2f} (Total: ${total_cost:.2f})"
            status = ActionStatus.PENDING
        else:
            description = f"ATTEMPTED BUY {quantity} shares of {ticker} - Insufficient funds (${portfolio_after.cash:.2f} < ${total_cost:.2f})"
            status = ActionStatus.PENDING

    elif action_type == ActionType.SELL:
        current_holdings = portfolio_after.holdings.get(ticker, 0)
        if current_holdings >= quantity:
            portfolio_after.cash += total_cost
            portfolio_after.holdings[ticker] = current_holdings - quantity
            if portfolio_after.holdings[ticker] == 0:
                del portfolio_after.holdings[ticker]
            description = f"SELL {quantity} shares of {ticker} at ${price:.2f} (Total: ${total_cost:.2f})"
            status = ActionStatus.PENDING
        else:
            description = f"ATTEMPTED SELL {quantity} shares of {ticker} - Insufficient holdings ({current_holdings} shares)"
            status = ActionStatus.PENDING

    elif action_type == ActionType.HOLD:
        description = f"HOLD positions for {ticker}"
        status = ActionStatus.PENDING

    # Create trading action
    action = {
        "id": action_id,
        "agent_id": model_id,
        "agent_name": _get_model_name(model_id),
        "agent_type": "trading_agent",
        "action": action_type.value,
        "description": description,
        "status": status.value,
        "timestamp": datetime.now().isoformat(),
        "targets": [ticker],
        "metadata": {
            "ticker": ticker,
            "action_type": action_type.value,
            "quantity": quantity,
            "price": price,
            "reasoning": reasoning,
            "portfolio_before": {
                "cash": portfolio_before.cash,
                "holdings": dict(portfolio_before.holdings),
            },
            "portfolio_after": {
                "cash": portfolio_after.cash,
                "holdings": dict(portfolio_after.holdings),
            },
            "total_cost": total_cost,
        },
    }

    # Add to storage
    TRADING_ACTIONS.append(action)

    # Update portfolio only if action is valid
    if action_type != ActionType.HOLD and total_cost > 0:
        if (action_type == ActionType.BUY and portfolio_before.cash >= total_cost) or (
            action_type == ActionType.SELL
            and portfolio_before.holdings.get(ticker, 0) >= quantity
        ):
            MODEL_PORTFOLIOS[model_id] = portfolio_after

    return action_id


def _get_model_name(model_id: str) -> str:
    """Get human readable model name."""
    name_mapping = {
        "claude-3.5-sonnet": "Claude 3.5 Sonnet",
        "gpt-4": "GPT-4",
        "gemini-1.5-pro": "Gemini 1.5 Pro",
        "claude-4-haiku": "Claude 4 Haiku",
    }
    return name_mapping.get(model_id, model_id)


def get_model_portfolio(model_id: str) -> Portfolio:
    """Get current portfolio for a model."""
    return MODEL_PORTFOLIOS.get(model_id, Portfolio(cash=100.0, holdings={}))


def update_action_status(action_id: str, new_status: ActionStatus) -> bool:
    """Update the status of a trading action."""
    for action in TRADING_ACTIONS:
        if action["id"] == action_id:
            action["status"] = new_status.value
            return True
    return False


def get_trading_actions(
    agent_type: str = None, status: str = None, limit: int = 100, hours: int = 24
) -> List[Dict]:
    """Get trading actions from system logs - ONLY trading decisions."""

    # Filter actions by time window
    cutoff_time = datetime.now() - timedelta(hours=hours)
    recent_actions = []

    for action in TRADING_ACTIONS:
        action_time = datetime.fromisoformat(action["timestamp"])
        if action_time >= cutoff_time:
            recent_actions.append(action)

    # Apply filters
    filtered_actions = recent_actions

    if agent_type:
        filtered_actions = [
            a for a in filtered_actions if a["agent_type"] == agent_type
        ]

    if status:
        filtered_actions = [a for a in filtered_actions if a["status"] == status]

    # Sort by timestamp (newest first) and limit
    filtered_actions.sort(key=lambda x: x["timestamp"], reverse=True)

    return filtered_actions[:limit]


# Sample actions removed - system logs will be empty until models generate real actions

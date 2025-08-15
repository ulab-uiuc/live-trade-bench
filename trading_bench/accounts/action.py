# ----------------------------------------------
# trading/utils.py
# ----------------------------------------------
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Sequence, TypeVar, Union


@dataclass
class StockAction:
    """Stock trading action with ticker, action type, timestamp, price and quantity."""

    ticker: str
    action: str  # "buy" or "sell"
    timestamp: str
    price: float
    quantity: float = 1.0
    confidence: float = 0.5

    def __post_init__(self):
        """Validate stock action fields."""
        if self.action.lower() not in ("buy", "sell"):
            raise ValueError(f"Invalid action: {self.action}")
        if self.price <= 0:
            raise ValueError(f"Invalid price: {self.price}")
        if self.quantity <= 0:
            raise ValueError(f"Invalid quantity: {self.quantity}")


@dataclass
class PolymarketAction:
    """Polymarket prediction market action with market_id, outcome, action, timestamp, price and quantity."""

    market_id: str
    outcome: str  # "yes" or "no"
    action: str  # "buy" or "sell"
    timestamp: str
    price: float  # range 0-1
    quantity: float = 1.0
    confidence: float = 0.5

    def __post_init__(self):
        """Validate polymarket action fields."""
        if self.outcome.lower() not in ("yes", "no"):
            raise ValueError(f"Invalid outcome: {self.outcome}")
        if self.action.lower() not in ("buy", "sell"):
            raise ValueError(f"Invalid action: {self.action}")
        if not (0 <= self.price <= 1):
            raise ValueError(f"Invalid price range: {self.price} (must be 0-1)")
        if self.quantity <= 0:
            raise ValueError(f"Invalid quantity: {self.quantity}")
        if not (0 <= self.confidence <= 1):
            raise ValueError(f"Invalid confidence: {self.confidence}")


# Type variable for action classes
T = TypeVar("T", StockAction, PolymarketAction)


def parse_actions(
    actions: Union[str, dict, List[dict], Sequence[T]], action_type: type[T]
) -> List[T]:
    """
    Parse actions from various input formats into Action class instances.

    Args:
        actions: JSON string, single dict, list of dicts, or sequence of Action instances
        action_type: The Action class to convert to (StockAction or PolymarketAction)

    Returns:
        List of Action instances

    Raises:
        ValueError: If actions format is invalid or conversion fails
    """
    try:
        # Parse JSON string
        if isinstance(actions, str):
            actions = json.loads(actions)

        # Convert single action to list
        if isinstance(actions, dict):
            actions = [actions]

        # If already Action instances, return as-is
        if actions and isinstance(actions[0], action_type):
            return list(actions)

        # Validate actions is a list
        if not isinstance(actions, (list, tuple)):
            raise ValueError(
                "Actions must be a string, dict, list of dicts, or sequence of Action instances"
            )

        # Convert dicts to Action instances
        result = []
        for i, action in enumerate(actions):
            if isinstance(action, action_type):
                result.append(action)
            elif isinstance(action, dict):
                try:
                    # Handle different action types
                    if action_type == StockAction:
                        result.append(
                            StockAction(
                                ticker=action["ticker"],
                                action=action["action"],
                                timestamp=action["timestamp"],
                                price=action.get("price", 0.0),
                                quantity=action.get("quantity", 1.0),
                            )
                        )
                    elif action_type == PolymarketAction:
                        result.append(
                            PolymarketAction(
                                market_id=action["market_id"],
                                outcome=action["outcome"],
                                action=action["action"],
                                timestamp=action["timestamp"],
                                price=action["price"],
                                quantity=action.get("quantity", 1.0),
                                confidence=action.get("confidence", 0.5),
                            )
                        )
                    else:
                        raise ValueError(f"Unsupported action type: {action_type}")
                except KeyError as e:
                    raise ValueError(f"Action {i} missing required field: {e}")
                except Exception as e:
                    raise ValueError(f"Error converting action {i}: {e}")
            else:
                raise ValueError(
                    f"Action {i} must be a dict or {action_type.__name__} instance"
                )

        return result

    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {e}")
    except Exception as e:
        raise ValueError(f"Error parsing actions: {e}")


def validate_stock_action(action: StockAction) -> bool:
    """
    Validate a stock action.

    Args:
        action: StockAction instance

    Returns:
        True if valid, False otherwise
    """
    try:
        # Basic validation (post_init already handles field validation)
        return (
            action.ticker
            and action.action.lower() in ("buy", "sell")
            and action.timestamp
            and action.price > 0
            and action.quantity > 0
        )
    except Exception:
        return False


def validate_polymarket_action(action: PolymarketAction) -> bool:
    """
    Validate a polymarket action.

    Args:
        action: PolymarketAction instance

    Returns:
        True if valid, False otherwise
    """
    try:
        # Basic validation (post_init already handles field validation)
        return (
            action.market_id
            and action.outcome.lower() in ("yes", "no")
            and action.action.lower() in ("buy", "sell")
            and action.timestamp
            and 0 <= action.price <= 1
            and action.quantity > 0
            and 0 <= action.confidence <= 1
        )
    except Exception:
        return False


# Convenience functions for backward compatibility
def to_dict(action: Union[StockAction, PolymarketAction]) -> Dict[str, Any]:
    """Convert Action instance to dictionary."""
    from dataclasses import asdict

    return asdict(action)


def from_dict(data: Dict[str, Any], action_type: type[T]) -> T:
    """Convert dictionary to Action instance."""
    return parse_actions([data], action_type)[0]

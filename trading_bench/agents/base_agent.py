from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, Tuple, TypeVar

from ..accounts import BaseAccount

# Generic types for different action and account types
ActionType = TypeVar("ActionType")
AccountType = TypeVar("AccountType", bound=BaseAccount)
DataType = TypeVar("DataType")


class BaseAgent(ABC, Generic[ActionType, AccountType, DataType]):
    """Unified base class for LLM-driven trading agents."""

    # Shared tuning knobs
    price_epsilon: float = 0.01  # ignore tiny price moves
    max_history: int = 10  # rolling price history per id

    def __init__(self, name: str, model_name: str = "gpt-4o-mini"):
        self.name = name
        self.model_name = model_name
        self.available = True
        self._history: Dict[str, List[float]] = {}
        self._last_price: Dict[str, float] = {}

    # -------------------- Public entry point --------------------
    def generate_action(
        self, data: DataType, account: AccountType
    ) -> Optional[ActionType]:
        """
        Unified generate_action:
        1) Extract id+price (domain-specific via hook)
        2) Gate on price change
        3) Prepare analysis text (hook) and call LLM with JSON-only system prompt (hook)
        4) Parse -> create domain action (hook)
        5) Fallback on errors/unavailable
        """
        _id, price = self._extract_id_price(data)

        # Gate on negligible price changes
        last = self._last_price.get(_id)
        if last is not None and abs(price - last) < self.price_epsilon:
            print(
                f"💤 {self.name}: {_id} price unchanged at {self._fmt_price(price)}, no action"
            )
            return None

        # Track price + history
        self._last_price[_id] = price
        h = self._history.setdefault(_id, [])
        h.append(price)
        if len(h) > self.max_history:
            self._history[_id] = h[-self.max_history :]

        print(
            f"📈 {self.name}: {_id} price changed to {self._fmt_price(price)}, analyzing..."
        )

        # If LLM is unavailable, skip action
        if not self.available:
            return None

        try:
            analysis = self._prepare_analysis_data(data, account)
            messages = [
                {"role": "system", "content": self._get_system_prompt(analysis)},
                {"role": "user", "content": analysis},
            ]
            llm_response = self._call_llm(messages)
            parsed = self._parse_llm_response(llm_response)
            print(parsed)
            if parsed:
                action = self._create_action_from_response(parsed, _id, price)
                if action:
                    self._log_action("LLM decision", details=str(action))
                return action

            return None

        except Exception as e:
            self._log_error(f"LLM error for {_id}", str(e))
            return None

    # -------------------- LLM utilities --------------------
    def _call_llm(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Call LLM with error handling

        Args:
            messages: List of message dicts with role and content

        Returns:
            Dict with success status and response/error
        """
        if not self.available:
            return {"success": False, "content": "", "error": "LLM not available"}

        try:
            from ..utils import call_llm

            return call_llm(messages, self.model_name, self.name)
        except Exception as e:
            return {"success": False, "content": "", "error": str(e)}

    def _parse_llm_response(
        self, llm_response: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Parse LLM response with error handling

        Args:
            llm_response: Response from _call_llm

        Returns:
            Parsed decision dict or None if failed
        """
        if not llm_response.get("success"):
            return None

        try:
            from ..utils import parse_trading_response

            return parse_trading_response(llm_response["content"])
        except Exception as e:
            print(f"⚠️ {self.name}: Failed to parse LLM response: {e}")
            return None

    # -------------------- Hooks for subclasses --------------------
    @abstractmethod
    def _extract_id_price(self, data: DataType) -> Tuple[str, float]:
        """Return a tuple (id, price) for gating/history/prints."""
        pass

    @abstractmethod
    def _prepare_analysis_data(self, data: DataType, account: AccountType) -> str:
        """Prepare analysis text for the LLM user message (you can use helpers like history_tail/prev_price)."""
        pass

    @abstractmethod
    def _create_action_from_response(
        self, parsed: Dict[str, Any], _id: str, price: float
    ) -> Optional[ActionType]:
        """Turn parsed JSON dict into a domain action (StockAction / PolymarketAction / etc.)."""
        pass

    @abstractmethod
    def _get_system_prompt(self, analysis: str) -> str:
        """Build the system prompt for LLM."""
        pass

    # -------------------- Helpers available to subclasses --------------------
    def history_tail(self, _id: str, k: int = 5) -> List[float]:
        """Return the last k prices for id."""
        return self._history.get(_id, [])[-k:]

    def prev_price(self, _id: str) -> Optional[float]:
        """Return the previous price if available."""
        hist = self._history.get(_id, [])
        return hist[-2] if len(hist) >= 2 else None

    def _fmt_price(self, price: float) -> str:
        """Format price for prints; override for probability-style markets."""
        return f"{price:.2f}"  # probability display

    # -------------------- Logging & metadata --------------------
    def _log_error(self, error_msg: str, context: str = "") -> None:
        context_str = f" | {context}" if context else ""
        print(f"⚠️ {self.name}: {error_msg}{context_str}")

    def _log_action(self, action_type: str, details: str = "") -> None:
        details_str = f": {details}" if details else ""
        print(f"💡 {self.name}: {action_type}{details_str}")

    @property
    def is_available(self) -> bool:
        return self.available

    def get_agent_info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "model_name": self.model_name,
            "available": self.available,
            "type": self.__class__.__name__,
        }

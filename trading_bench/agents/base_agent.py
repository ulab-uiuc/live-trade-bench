"""
Base Agent class for trading agents
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar

from ..accounts import BaseAccount

# Generic types for different action and account types
ActionType = TypeVar("ActionType")
AccountType = TypeVar("AccountType", bound=BaseAccount)
DataType = TypeVar("DataType")


class BaseAgent(ABC, Generic[ActionType, AccountType, DataType]):
    """Abstract base class for trading agents"""

    def __init__(self, name: str, model_name: str = "gpt-4o-mini"):
        self.name = name
        self.model_name = model_name
        self.available = True

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
        if not llm_response["success"]:
            return None

        try:
            from ..utils import parse_trading_response

            return parse_trading_response(llm_response["content"])
        except Exception as e:
            print(f"⚠️ {self.name}: Failed to parse LLM response: {e}")
            return None

    @abstractmethod
    def generate_action(
        self, data: DataType, account: AccountType
    ) -> Optional[ActionType]:
        """
        Generate trading action based on data and account state

        Args:
            data: Market/price data for analysis
            account: Account to trade with

        Returns:
            Trading action or None
        """
        pass

    @abstractmethod
    def _prepare_analysis_data(self, data: DataType, account: AccountType) -> str:
        """
        Prepare analysis data for LLM

        Args:
            data: Market/price data
            account: Account state

        Returns:
            Formatted analysis string for LLM
        """
        pass

    @abstractmethod
    def _get_system_prompt(self) -> str:
        """
        Get system prompt for LLM

        Returns:
            System prompt string
        """
        pass

    def _log_error(self, error_msg: str, context: str = "") -> None:
        """
        Log error with consistent formatting

        Args:
            error_msg: Error message
            context: Additional context (e.g., ticker, market_id)
        """
        context_str = f" for {context}" if context else ""
        print(f"⚠️ {self.name}: {error_msg}{context_str}")

    def _log_action(self, action_type: str, details: str = "") -> None:
        """
        Log trading action with consistent formatting

        Args:
            action_type: Type of action taken
            details: Additional details
        """
        details_str = f": {details}" if details else ""
        print(f"💡 {self.name}: {action_type}{details_str}")

    @property
    def is_available(self) -> bool:
        """Check if agent is available for trading"""
        return self.available

    def get_agent_info(self) -> Dict[str, Any]:
        """
        Get basic agent information

        Returns:
            Dict with agent details
        """
        return {
            "name": self.name,
            "model_name": self.model_name,
            "available": self.available,
            "type": self.__class__.__name__,
        }

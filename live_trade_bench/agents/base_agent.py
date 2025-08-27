from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar

from ..accounts import BaseAccount

AccountType = TypeVar("AccountType", bound=BaseAccount[Any, Any])
DataType = TypeVar("DataType")


class BaseAgent(ABC, Generic[AccountType, DataType]):
    price_epsilon: float = 0.01
    max_history: int = 10

    def __init__(self, name: str, model_name: str = "gpt-4o-mini") -> None:
        self.name = name
        self.model_name = model_name
        self.available = True

    def generate_portfolio_allocation(
        self, market_data: Dict[str, DataType], account: AccountType
    ) -> Optional[Dict[str, float]]:
        """Generate complete portfolio allocation for all assets."""
        if not market_data:
            print(f"💤 No market data available for {self.name}")
            return None

        if not self.available:
            return None

        try:
            # Prepare comprehensive analysis
            market_analysis = self._prepare_market_analysis(market_data)
            account_analysis = self._prepare_account_analysis(account)
            full_analysis = self._combine_analysis_data(
                market_analysis, account_analysis
            )

            messages = [
                {
                    "role": "user",
                    "content": self._get_portfolio_prompt(full_analysis, market_data),
                }
            ]

            print(f"🔍 {self.name}: Calling LLM with {len(market_data)} assets...")
            llm_response = self._call_llm(messages)

            if not llm_response.get("success"):
                print(
                    f"❌ {self.name}: LLM call failed: {llm_response.get('error', 'Unknown error')}"
                )
                return None

            print(
                f"✅ {self.name}: LLM response received, length: {len(llm_response.get('content', ''))}"
            )

            parsed = self._parse_portfolio_response(llm_response)

            if not parsed:
                print(f"❌ {self.name}: Failed to parse LLM response")
                return None

            print(f"✅ {self.name}: Response parsed successfully: {parsed}")

            portfolio_allocation = self._create_portfolio_allocation_from_response(
                parsed, market_data
            )

            if portfolio_allocation:
                print(
                    f"🤖 {self.name}: Generated portfolio allocation: {portfolio_allocation}"
                )
            else:
                print(f"🤖 {self.name}: No portfolio allocation generated")
            return portfolio_allocation
        except Exception as e:
            self._log_error("LLM error", str(e))
            return None

    # ----- LLM plumbing -----
    def _call_llm(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        if not self.available:
            return {"success": False, "content": "", "error": "LLM not available"}
        try:
            from ..utils import call_llm

            return call_llm(messages, self.model_name, self.name)
        except Exception as e:
            return {"success": False, "content": "", "error": str(e)}

    def _parse_portfolio_response(
        self, llm_response: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        if not llm_response.get("success"):
            return None
        try:
            from ..utils import parse_portfolio_response

            return parse_portfolio_response(llm_response["content"])
        except Exception as e:
            self._log_error("parse error", str(e))
            return None

    # ----- Analysis Methods -----
    @abstractmethod
    def _prepare_market_analysis(self, market_data: Dict[str, DataType]) -> str:
        """Prepare comprehensive market data analysis for all assets."""
        ...

    def _prepare_account_analysis(self, account: AccountType) -> str:
        """Prepare account analysis with portfolio info."""
        positions = account.get_active_positions()
        total_positions = len(positions)
        portfolio_value = account.get_total_value()
        profit_loss = portfolio_value - account.cash_balance

        return (
            f"ACCOUNT INFO:\n"
            f"  Cash: ${account.cash_balance:.2f}\n"
            f"  Portfolio Value: ${portfolio_value:.2f}\n"
            f"  P&L: ${profit_loss:+.2f}\n"
            f"  Total Positions: {total_positions}\n"
            f"  Current Allocations: {account.target_allocations}"
        )

    def _combine_analysis_data(
        self, market_analysis: str, account_analysis: str
    ) -> str:
        """Combine all analysis data into final format."""
        return f"{market_analysis}\n\n{account_analysis}"

    # ----- Hooks -----
    @abstractmethod
    def _create_portfolio_allocation_from_response(
        self, parsed: Dict[str, Any], market_data: Dict[str, DataType]
    ) -> Optional[Dict[str, float]]:
        """Create complete portfolio allocation from LLM response."""
        ...

    @abstractmethod
    def _get_portfolio_prompt(
        self, analysis: str, market_data: Dict[str, DataType]
    ) -> str:
        """Get portfolio allocation prompt for all assets."""
        ...

    def _log_error(self, msg: str, ctx: str = "") -> None:
        if ctx:
            msg = f"{msg} | {ctx}"
        print(f"⚠️ {self.name}: {msg}")

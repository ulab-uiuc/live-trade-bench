from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any, Dict, Generic, List, Optional, TypeVar

from ..accounts import BaseAccount
from ..utils.agent_utils import normalize_allocations, parse_llm_response_to_json

AccountType = TypeVar("AccountType", bound=BaseAccount[Any, Any])
DataType = TypeVar("DataType")


class BaseAgent(ABC, Generic[AccountType, DataType]):
    def __init__(self, name: str, model_name: str = "gpt-4o-mini") -> None:
        self.name = name
        self.model_name = model_name
        self.available = True
        self._history: Dict[str, List[float]] = {}
        self._last_price: Dict[str, float] = {}
        self.price_history: Dict[str, List[float]] = defaultdict(list)

    def generate_allocation(
        self,
        market_data: Dict[str, DataType],
        account_data: Dict[str, Any],
        date: str | None = None,
        news_data: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, float]]:
        if not market_data or not self.available:
            return None

        try:
            market_analysis = self._prepare_market_analysis(market_data)
            account_analysis = self._prepare_account_analysis(account_data)
            news_analysis = self._prepare_news_analysis(market_data, news_data)
            full_analysis = self._combine_analysis_data(
                market_analysis, account_analysis, news_analysis
            )

            messages = [
                {
                    "role": "user",
                    "content": self._get_portfolio_prompt(full_analysis, market_data),
                }
            ]
            print("\n--- LLM PROMPT ---")
            print(messages[0]["content"])
            print("--- END LLM PROMPT ---\n")

            llm_response = self._call_llm(messages)
            if not llm_response.get("success"):
                self._log_error(
                    "LLM call failed", llm_response.get("error", "Unknown error")
                )
                return None

            parsed = self._parse_allocation_response(llm_response)
            if not parsed:
                self._log_error("Failed to parse LLM response")
                return None

            return normalize_allocations(parsed)
        except Exception as e:
            self._log_error("LLM error", str(e))
            return None

    def _call_llm(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        if not self.available:
            return {"success": False, "content": "", "error": "LLM not available"}
        try:
            from ..utils import call_llm

            return call_llm(messages, self.model_name, self.name)
        except Exception as e:
            return {"success": False, "content": "", "error": str(e)}

    def _parse_allocation_response(
        self, llm_response: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        content = llm_response.get("content", "")
        if not llm_response.get("success") or not content:
            return None

        parsed = parse_llm_response_to_json(content)
        if not parsed:
            self._log_error("JSON parsing failed", f"Content: {content}")
        return parsed

    @abstractmethod
    def _prepare_market_analysis(self, market_data: Dict[str, DataType]) -> str:
        ...

    def _prepare_account_analysis(self, account_data: Dict[str, Any]) -> str:
        return (
            f"ACCOUNT INFO:\n"
            f"  Cash: ${account_data.get('cash_balance', 0.0):.2f}\n"
            f"  Portfolio Value: ${account_data.get('total_value', 0.0):.2f}\n"
            f"  P&L: ${account_data.get('pnl', 0.0):+.2f}\n"
            f"  Total Positions: {account_data.get('total_positions', 0)}\n"
            f"  Current Allocations: {account_data.get('target_allocations', {})}"
        )

    def _prepare_news_analysis(
        self,
        market_data: Dict[str, Any],
        news_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        try:
            news_summaries = []
            if news_data:
                for asset_id, articles in list(news_data.items())[:3]:
                    display_name = market_data.get(asset_id, {}).get(
                        "question", asset_id
                    )
                    if articles:
                        snippet = articles[0].get("snippet", "")
                        news_summaries.append(f"• {display_name}: {snippet[:100]}...")
                    else:
                        news_summaries.append(f"• {display_name}: No recent news")
            else:
                for asset_id in list(market_data.keys())[:3]:
                    display_name = market_data.get(asset_id, {}).get(
                        "question", asset_id
                    )
                    news_summaries.append(f"• {display_name}: No news data provided")

            return "RECENT NEWS:\n" + "\n".join(news_summaries)

        except Exception as e:
            print(f"Error preparing news analysis: {e}")
            return "RECENT NEWS: Error preparing news analysis."

    def _create_news_query(self, asset_id: str, data: DataType) -> str:
        return asset_id

    def _combine_analysis_data(
        self, market_analysis: str, account_analysis: str, news_analysis: str
    ) -> str:
        return f"{market_analysis}\n\n{account_analysis}\n\n{news_analysis}"

    @abstractmethod
    def _get_portfolio_prompt(
        self, analysis: str, market_data: Dict[str, DataType]
    ) -> str:
        ...

    def prev_price(self, ticker: str) -> Optional[float]:
        history = self.price_history.get(ticker)
        return history[-1] if history else None

    def history_tail(self, ticker: str, n: int) -> List[float]:
        history = self.price_history.get(ticker, [])
        return history[-n:]

    def _update_price_history(self, ticker: str, price: float) -> None:
        self.price_history[ticker].append(price)

    def _log_error(self, msg: str, ctx: str = "") -> None:
        if ctx:
            msg = f"{msg} | {ctx}"
        print(f"⚠️ {self.name}: {msg}")

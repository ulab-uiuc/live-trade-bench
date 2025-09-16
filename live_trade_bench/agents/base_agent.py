from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import datetime
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
        self.last_llm_input = None
        self.last_llm_output = None

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
                    "content": self._get_portfolio_prompt(full_analysis, market_data, date),
                }
            ]
            
            # Save LLM input for recording
            self.last_llm_input = {
                "prompt": messages[0]["content"],
                "model": self.model_name,
                "timestamp": datetime.now().isoformat()
            }
            
            print("\n--- LLM PROMPT ---")
            print(messages[0]["content"])
            print("--- END LLM PROMPT ---\n")

            llm_response = self._call_llm(messages)
            
            # Save LLM output for recording
            self.last_llm_output = {
                "success": llm_response.get("success", False),
                "content": llm_response.get("content", ""),
                "error": llm_response.get("error", None),
                "timestamp": datetime.now().isoformat()
            }
            
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
        allocation_history = account_data.get("allocation_history", [])
        current_performance = account_data.get("performance", 0.0)

        if allocation_history:
            recent_allocations = allocation_history[-10:]  # Get last 10 records
            all_allocations = []
            for i, snapshot in enumerate(recent_allocations):
                timestamp = snapshot.get("timestamp", f"Record {i+1}")
                allocations = snapshot.get("allocations", {})
                performance = snapshot.get("performance", 0.0)

                # Format allocations with 2 decimal places
                formatted_allocations = {}
                for key, value in allocations.items():
                    formatted_allocations[key] = f"{value:.2f}"

                all_allocations.append(
                    f"    Allocation at last {len(recent_allocations)-i}th time: {formatted_allocations} (Return rate: {performance:.1f}%)"
                )

            allocations_text = "\n".join(all_allocations)

            return (
                f"ACCOUNT INFO:\n"
                f"  Current return rate: {current_performance:.1f}%\n"
                f"  Recent Ten Historical Allocations:\n{allocations_text}"
            )
        else:
            return (
                f"ACCOUNT INFO:\n"
                f"  Current return rate: {current_performance:.1f}%\n"
                f"  Recent Ten Historical Allocations: No history available"
            )

    def _prepare_news_analysis(
        self,
        market_data: Dict[str, Any],
        news_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        if not news_data:
            return "RECENT NEWS: No news data available."

        news_summaries = []
        for asset_id, articles in news_data.items():
            display_name = market_data.get(asset_id, {}).get("question", asset_id)

            if not articles:
                news_summaries.append(f"• {display_name}: No recent news")
                continue

            for i, article in enumerate(articles[:3]):
                title = article.get("title", "")
                snippet = article.get("snippet", "")
                date_timestamp = article.get("date")
                
                # Format the date for display
                date_str = ""
                if date_timestamp:
                    try:
                        from datetime import datetime
                        news_date = datetime.fromtimestamp(date_timestamp)
                        date_str = f" ({news_date.strftime('%Y-%m-%d')})"
                    except:
                        pass

                if i == 0:
                    news_summaries.append(f"• {display_name}:\n  - {title}{date_str}")
                else:
                    news_summaries.append(f"  - {title}{date_str}")

                if snippet:
                    news_summaries.append(f"    {snippet}...")

        return "RECENT NEWS:\n" + "\n".join(news_summaries)

    def _format_price_history(
        self, price_history: List[Dict], ticker: str, is_stock: bool = True
    ) -> List[str]:
        """Format price history with relative day descriptions"""
        lines = []

        if price_history:
            # price_history is already in chronological order (oldest to newest)
            # We want to display from newest to oldest
            recent_history = price_history[-10:]  # Get last 10 days
            for i, h in enumerate(
                reversed(recent_history)
            ):  # Reverse to show newest first
                hist_price = h.get("price", 0.0)
                hist_date = h.get("date", "Unknown Date")

                if is_stock:
                    price_str = f"close price ${hist_price:,.2f}"
                else:
                    price_str = f"{hist_price:.4f}"

                # Calculate change from previous day if possible
                change_str = "N/A"
                # The previous day is the next element in the reversed list,
                # or the one before the current in the original recent_history
                original_index = len(recent_history) - 1 - i
                if original_index > 0:
                    prev_day_price = recent_history[original_index - 1].get("price", 0.0)
                    if prev_day_price > 0:
                        change = hist_price - prev_day_price
                        change_pct = (change / prev_day_price) * 100
                        change_str = f"{change:+.2f} ({change_pct:+.2f}%)"

                lines.append(f"  - {hist_date}: {price_str} (Change: {change_str})")
        else:
            # Also update the history for the current price if available
            current_price = self.history_tail(ticker, 1)
            if current_price:
                price = current_price[0]
                price_str = f"${price:,.2f}" if is_stock else f"{price:.3f}"
                lines.append(f"  - Current Price: {price_str}")

        return lines

    def _create_news_query(self, asset_id: str, data: DataType) -> str:
        return asset_id

    def _combine_analysis_data(
        self, market_analysis: str, account_analysis: str, news_analysis: str
    ) -> str:
        return f"{market_analysis}\n\n{news_analysis}\n\n{account_analysis}"

    @abstractmethod
    def _get_portfolio_prompt(
        self, analysis: str, market_data: Dict[str, DataType], date: Optional[str] = None
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

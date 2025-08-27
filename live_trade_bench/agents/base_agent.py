from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar

from ..accounts import BaseAccount

AccountType = TypeVar("AccountType", bound=BaseAccount[Any, Any])
DataType = TypeVar("DataType")


class BaseAgent(ABC, Generic[AccountType, DataType]):
    def __init__(self, name: str, model_name: str = "gpt-4o-mini") -> None:
        self.name = name
        self.model_name = model_name
        self.available = True
        self._history: Dict[str, List[float]] = {}
        self._last_price: Dict[str, float] = {}
        self.account = None  # Will be set by the system

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
            # Display current portfolio value before generating new allocation
            current_value = account.get_total_value()
            print(f"💰 {self.name} current portfolio value: ${current_value:,.2f}")

            # Prepare comprehensive analysis
            market_analysis = self._prepare_market_analysis(market_data)
            account_analysis = self._prepare_account_analysis(account)
            news_analysis = self._prepare_news_analysis(market_data)
            full_analysis = self._combine_analysis_data(
                market_analysis, account_analysis, news_analysis
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

    def _prepare_news_analysis(self, market_data: Dict[str, DataType]) -> str:
        """Prepare news analysis for all assets."""
        try:
            from datetime import datetime, timedelta

            from ..fetchers.news_fetcher import fetch_news_data

            # Get recent news (last 3 days)
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")

            news_summaries = []
            for asset_id, data in list(market_data.items())[:3]:  # Top 3 assets
                query = self._create_news_query(asset_id, data)
                news = fetch_news_data(query, start_date, end_date, max_pages=1)

                if news:
                    # Summarize top news item
                    snippet = news[0].get("snippet", "")
                    news_summaries.append(f"• {asset_id}: {snippet[:100]}...")
                else:
                    news_summaries.append(f"• {asset_id}: No recent news")

            return "RECENT NEWS:\n" + "\n".join(news_summaries)

        except Exception as e:
            return f"RECENT NEWS:\n• News fetch error: {str(e)}..."

    def _create_news_query(self, asset_id: str, data: DataType) -> str:
        """Create news search query. Override in subclasses for domain-specific queries."""
        return asset_id

    def _combine_analysis_data(
        self, market_analysis: str, account_analysis: str, news_analysis: str
    ) -> str:
        """Combine all analysis data into final format."""
        return f"{market_analysis}\n\n{account_analysis}\n\n{news_analysis}"

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

    # ----- Helpers -----
    def history_tail(self, asset_id: str, k: int = 5) -> List[float]:
        """Get last k price values for an asset."""
        return self._history.get(asset_id, [])[-k:]

    def prev_price(self, asset_id: str) -> Optional[float]:
        """Get previous price for an asset."""
        hist = self._history.get(asset_id, [])
        return hist[-2] if len(hist) >= 2 else None

    def _update_price_history(self, asset_id: str, price: float) -> None:
        """Update price history for an asset."""
        if asset_id not in self._history:
            self._history[asset_id] = []

        self._history[asset_id].append(price)

        # Keep only last 10 prices
        if len(self._history[asset_id]) > 10:
            self._history[asset_id] = self._history[asset_id][-10:]

        self._last_price[asset_id] = price

    def _log_error(self, msg: str, ctx: str = "") -> None:
        if ctx:
            msg = f"{msg} | {ctx}"
        print(f"⚠️ {self.name}: {msg}")

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, Tuple, TypeVar

from ..accounts import BaseAccount

ActionType = TypeVar("ActionType")
AccountType = TypeVar("AccountType", bound=BaseAccount)
DataType = TypeVar("DataType")


class BaseAgent(ABC, Generic[ActionType, AccountType, DataType]):
    price_epsilon: float = 0.01
    max_history: int = 10

    def __init__(self, name: str, model_name: str = "gpt-4o-mini") -> None:
        self.name = name
        self.model_name = model_name
        self.available = True
        self._history: Dict[str, List[float]] = {}
        self._last_price: Dict[str, float] = {}

    def generate_action(
        self, data: DataType, account: AccountType
    ) -> Optional[ActionType]:
        _id, price = self._extract_id_price(data)

        last = self._last_price.get(_id)
        if last is not None and abs(price - last) < self.price_epsilon:
            print(f"💤 no action for {_id} since no price change")
            return None

        self._last_price[_id] = price
        h = self._history.setdefault(_id, [])
        h.append(price)
        if len(h) > self.max_history:
            self._history[_id] = h[-self.max_history :]

        if not self.available:
            return None

        try:
            market_analysis = self._prepare_market_analysis(data)
            account_analysis = self._prepare_account_analysis(account)
            news_analysis = self._prepare_news_analysis(_id, data)
            full_analysis = self._combine_analysis_data(
                market_analysis, account_analysis, news_analysis
            )

            messages = [{"role": "user", "content": self._get_prompt(full_analysis)}]
            llm_response = self._call_llm(messages)
            parsed = self._parse_llm_response(llm_response)

            if parsed:
                action = self._create_action_from_response(parsed, _id, price)
                if action:
                    print(
                        f"🤖 {self.name} ({_id}): {action.action.upper()} {action.quantity} {getattr(action, 'outcome', 'shares').upper()}"
                    )
                else:
                    # hold
                    print(f"🤖 {self.name} ({_id}): HOLD")
                return action
            return None
        except Exception as e:
            self._log_error(f"LLM error for {_id}", str(e))
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

    def _parse_llm_response(
        self, llm_response: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        if not llm_response.get("success"):
            return None
        try:
            from ..utils import parse_trading_response

            return parse_trading_response(llm_response["content"])
        except Exception as e:
            self._log_error("parse error", str(e))
            return None

    # ----- Analysis Methods -----
    @abstractmethod
    def _prepare_market_analysis(self, data: DataType) -> str:
        """Prepare market data analysis."""
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
            f"  Total Positions: {total_positions}"
        )

    def _prepare_news_analysis(self, _id: str, data: DataType) -> str:
        """Prepare news analysis for the asset."""
        try:
            from datetime import datetime, timedelta

            from ..fetchers.news_fetcher import fetch_news_data

            # Get recent news (last 3 days)
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")

            # Create search query based on data type
            query = self._create_news_query(_id, data)

            news = fetch_news_data(query, start_date, end_date, max_pages=1)

            if news:
                # Summarize top 2 news items
                news_summary = []
                for article in news[:2]:
                    snippet = article.get("snippet", "")
                    news_summary.append(f"• {snippet}...")

                return "RECENT NEWS:\n" + "\n".join(news_summary)
            else:
                return "RECENT NEWS:\n• No recent news found"

        except Exception as e:
            return f"RECENT NEWS:\n• News fetch error: {str(e)}..."

    def _create_news_query(self, _id: str, data: DataType) -> str:
        """Create news search query. Override in subclasses for domain-specific queries."""
        return _id

    def _combine_analysis_data(
        self, market_analysis: str, account_analysis: str, news_analysis: str
    ) -> str:
        """Combine all analysis data into final format."""
        return f"{market_analysis}\n\n{account_analysis}\n\n{news_analysis}"

    # ----- Hooks -----
    @abstractmethod
    def _extract_id_price(self, data: DataType) -> Tuple[str, float]:
        ...

    @abstractmethod
    def _create_action_from_response(
        self, parsed: Dict[str, Any], _id: str, price: float
    ) -> Optional[ActionType]:
        ...

    @abstractmethod
    def _get_prompt(self, analysis: str) -> str:
        ...

    # ----- Helpers -----
    def history_tail(self, _id: str, k: int = 5) -> List[float]:
        return self._history.get(_id, [])[-k:]

    def prev_price(self, _id: str) -> Optional[float]:
        hist = self._history.get(_id, [])
        return hist[-2] if len(hist) >= 2 else None

    def _log_error(self, msg: str, ctx: str = "") -> None:
        if ctx:
            msg = f"{msg} | {ctx}"
        print(f"⚠️ {self.name}: {msg}")

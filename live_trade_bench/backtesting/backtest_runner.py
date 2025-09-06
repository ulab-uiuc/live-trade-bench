"""
Backtest Runner - Time simulation with ZERO special cases

Linus principle: "Good code has no special cases"
This just controls time flow, everything else uses existing systems unchanged.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List

from ..agents.stock_system import StockPortfolioSystem
from ..fetchers.stock_fetcher import StockFetcher


class BacktestRunner:
    """
    Time controller for backtesting. That's it. Nothing fancy.

    Existing StockPortfolioSystem + StockFetcher do all the work.
    We just control what "today" means.
    """

    def __init__(
        self,
        start_date: str,
        end_date: str,
        *,
        simulate_rebalance: bool = True,
        include_news: bool = False,
    ) -> None:
        """
        Args:
            start_date: YYYY-MM-DD
            end_date: YYYY-MM-DD
        """
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.end_date = datetime.strptime(end_date, "%Y-%m-%d")
        self.current_date = self.start_date
        self.simulate_rebalance = simulate_rebalance
        self.include_news = include_news

        # Reuse existing systems - no special cases
        self.portfolio_system = StockPortfolioSystem()
        self.stock_fetcher = StockFetcher()

        # Results storage
        self.daily_results: List[Dict[str, Any]] = []

    def add_agent(
        self, name: str, initial_cash: float = 1000.0, model_name: str = "gpt-4o-mini"
    ) -> None:
        """Add agent - same interface as live system."""
        self.portfolio_system.add_agent(name, initial_cash, model_name)

    async def run(self) -> Dict[str, Any]:
        """
        Run backtest. Pure simplicity.

        Just iterate through dates and let existing system do its job.
        """
        print(
            f"🚀 Starting backtest: {self.start_date.strftime('%Y-%m-%d')} → {self.end_date.strftime('%Y-%m-%d')}"
        )

        trading_days = self._get_trading_days()
        print(f"📅 Found {len(trading_days)} trading days")

        for day in trading_days:
            self.current_date = day
            day_str = day.strftime("%Y-%m-%d")

            print(f"\n📆 {day_str}")

            # Get historical market data for this specific day
            market_data = self._get_day_market_data(day)

            if not market_data:
                print(f"   ⚠️ No market data for {day_str}, skipping")
                continue

            print(f"   📊 Got data for {len(market_data)} stocks")

            # Debug: Show sample market data
            if market_data:
                sample_ticker = list(market_data.keys())[0]
                sample_price = market_data[sample_ticker]["current_price"]
                print(f"   💰 Sample: {sample_ticker} = ${sample_price:.2f}")

            # Run portfolio cycle with historical data - same as live system
            day_results = await self._run_day_cycle(day, market_data)
            self.daily_results.append(day_results)

        return self._generate_backtest_summary()

    def _get_trading_days(self) -> List[datetime]:
        """Get trading days in the backtest period."""
        days = []
        current = self.start_date

        while current <= self.end_date:
            # Skip weekends
            if current.weekday() < 5:  # Monday=0, Friday=4
                days.append(current)
            current += timedelta(days=1)

        return days

    def _get_day_market_data(self, date: datetime) -> Dict[str, Dict[str, Any]]:
        """
        Get market data for a specific day using existing StockFetcher.

        This is the beauty - we just ask StockFetcher for historical data!
        """
        day_str = date.strftime("%Y-%m-%d")
        next_day = (date + timedelta(days=1)).strftime("%Y-%m-%d")

        market_data = {}

        for ticker in self.portfolio_system.universe:
            try:
                # Use existing StockFetcher with historical date range
                df = self.stock_fetcher.fetch_stock_data(
                    ticker=ticker,
                    start_date=day_str,
                    end_date=next_day,  # Get just this day
                    interval="1d",
                )

                if df is not None and not df.empty:
                    # Extract the data - same format as live system
                    row = df.iloc[-1]  # Get the last (only) row

                    # Robust close extraction for different yfinance formats
                    close_val = None
                    try:
                        if "Close" in row:
                            val = row["Close"]
                            close_val = (
                                float(val.iloc[0])
                                if hasattr(val, "iloc")
                                else float(val)
                            )
                        elif "Adj Close" in row:
                            val = row["Adj Close"]
                            close_val = (
                                float(val.iloc[0])
                                if hasattr(val, "iloc")
                                else float(val)
                            )
                    except Exception:
                        close_val = None

                    if close_val is None:
                        # Fallback: try to coerce last numeric
                        try:
                            close_val = float(row.dropna().astype(float)[-1])
                        except Exception:
                            continue

                    info = self.portfolio_system.stock_info.get(ticker, {})
                    market_data[ticker] = {
                        "ticker": ticker,
                        "name": info.get("name", ticker),
                        "sector": info.get("sector", "Unknown"),
                        "current_price": close_val,
                        "market_cap": info.get("market_cap", 0),
                        "timestamp": date.isoformat(),
                    }

            except Exception as e:
                print(f"     ⚠️ Error fetching {ticker}: {e}")
                continue

        return market_data

    def _prepare_historical_news_analysis(
        self, date: datetime, market_data: Dict[str, Any]
    ) -> str:
        """
        Prepare historical news analysis - same format as BaseAgent._prepare_news_analysis()

        This maintains interface consistency with live system!
        """
        if not self.include_news:
            return "RECENT NEWS:\n• News disabled"

        try:
            from ..fetchers.news_fetcher import fetch_news_data

            day_str = date.strftime("%Y-%m-%d")
            news_summaries = []

            # Same logic as BaseAgent._prepare_news_analysis() but with historical date
            for asset_id, data in list(market_data.items())[:3]:  # Top 3 assets
                query = f"{asset_id} stock"  # Same as base agent
                try:
                    news = fetch_news_data(query, day_str, day_str, max_pages=1)

                    if news:
                        # Summarize top news item - same format as live system
                        snippet = news[0].get("snippet", "")
                        news_summaries.append(f"• {asset_id}: {snippet[:100]}...")
                    else:
                        news_summaries.append(f"• {asset_id}: No recent news")

                except Exception:
                    news_summaries.append(f"• {asset_id}: News fetch error")

            return "RECENT NEWS:\n" + "\n".join(news_summaries)

        except Exception as e:
            return f"RECENT NEWS:\n• News fetch error: {str(e)}..."

    async def _run_day_cycle(
        self, date: datetime, market_data: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Run one day's trading cycle.

        This uses the EXACT same logic as live system - no special cases!
        """
        day_str = date.strftime("%Y-%m-%d")

        day_results = {
            "date": day_str,
            "agents": {},
            "market_data_count": len(market_data),
        }

        # Update position prices for all agents
        for agent_name, agent in self.portfolio_system.agents.items():
            for ticker, data in market_data.items():
                price = data["current_price"]
                if hasattr(agent.account, "update_position_price"):
                    agent.account.update_position_price(ticker, price)

        # Generate portfolio allocations for all agents CONCURRENTLY 🚀
        async def process_agent_backtest(agent_name: str, agent) -> tuple[str, dict]:
            """Process a single agent in backtest"""
            try:
                # Override agent's news analysis to use historical date
                original_prepare_news = agent._prepare_news_analysis
                agent._prepare_news_analysis = (
                    lambda md: self._prepare_historical_news_analysis(date, md)
                )

                print(f"     🔍 {agent_name}: Processing concurrently...")

                # Same logic as StockPortfolioSystem.run_cycle() - no special cases!
                allocation = await agent.generate_portfolio_allocation(
                    market_data, agent.account
                )

                # Restore original method
                agent._prepare_news_analysis = original_prepare_news

                if allocation:
                    # Update target allocations
                    for ticker, target_ratio in allocation.items():
                        agent.account.set_target_allocation(ticker, target_ratio)

                    # Optionally simulate rebalancing to targets to generate positions/value
                    if self.simulate_rebalance and hasattr(
                        agent.account, "_simulate_rebalance_to_target"
                    ):
                        agent.account._simulate_rebalance_to_target(allocation)

                    # Record snapshot after applying
                    if hasattr(agent.account, "_record_allocation_snapshot"):
                        agent.account._record_allocation_snapshot()

                # Compute portfolio value
                portfolio_value = agent.account.get_total_value()
                agent_result = {
                    "portfolio_value": portfolio_value,
                    "cash_balance": agent.account.cash_balance,
                    "allocation": allocation,
                    "target_allocations": agent.account.target_allocations.copy(),
                }

                print(f"     ✅ {agent_name}: ${portfolio_value:,.2f}")
                return agent_name, agent_result

            except Exception as e:
                print(f"     ❌ {agent_name}: Error - {e}")
                import traceback

                traceback.print_exc()
                return agent_name, {
                    "portfolio_value": 0.0,
                    "cash_balance": 0.0,
                    "allocation": {},
                    "target_allocations": {},
                    "error": str(e),
                }

        # 🚀 Execute all agents concurrently!
        agent_tasks = [
            process_agent_backtest(agent_name, agent)
            for agent_name, agent in self.portfolio_system.agents.items()
        ]

        print(f"     🚀 Processing {len(agent_tasks)} agents concurrently...")
        agent_results = await asyncio.gather(*agent_tasks, return_exceptions=True)

        # Process results
        for result in agent_results:
            if isinstance(result, Exception):
                print(f"     ❌ Agent exception: {result}")
                continue
            if isinstance(result, tuple):
                agent_name, agent_data = result
                day_results["agents"][agent_name] = agent_data

        return day_results

    def _generate_backtest_summary(self) -> Dict[str, Any]:
        """Generate final backtest results."""
        if not self.daily_results:
            return {"error": "No results"}

        # Calculate performance metrics
        agent_names = list(self.portfolio_system.agents.keys())
        summary = {
            "start_date": self.start_date.strftime("%Y-%m-%d"),
            "end_date": self.end_date.strftime("%Y-%m-%d"),
            "total_days": len(self.daily_results),
            "agents": {},
        }

        for agent_name in agent_names:
            # Get first and last day results
            first_day = None
            last_day = None

            for day_result in self.daily_results:
                if (
                    agent_name in day_result["agents"]
                    and "portfolio_value" in day_result["agents"][agent_name]
                ):
                    if first_day is None:
                        first_day = day_result["agents"][agent_name]["portfolio_value"]
                    last_day = day_result["agents"][agent_name]["portfolio_value"]

            if first_day and last_day:
                total_return = last_day - first_day
                return_pct = (total_return / first_day) * 100 if first_day > 0 else 0

                summary["agents"][agent_name] = {
                    "initial_value": first_day,
                    "final_value": last_day,
                    "total_return": total_return,
                    "return_percentage": return_pct,
                }

        summary["daily_results"] = self.daily_results
        return summary

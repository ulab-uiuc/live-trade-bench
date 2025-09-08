"""
Backtest Runner - Simple time controller for both stock and polymarket

Linus principle: "Good code has no special cases"
Just controls time flow, uses existing systems unchanged.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List

from ..systems.polymarket_system import PolymarketPortfolioSystem
from ..systems.stock_system import StockPortfolioSystem


class BacktestRunner:
    def __init__(
        self,
        system: StockPortfolioSystem | PolymarketPortfolioSystem,
        start_date: str,
        end_date: str,
    ) -> None:
        self.system = system
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.end_date = datetime.strptime(end_date, "%Y-%m-%d")

    def run(self) -> Dict[str, Any]:
        trading_days = self._get_trading_days()
        market_type = (
            "stock" if isinstance(self.system, StockPortfolioSystem) else "polymarket"
        )

        for day in trading_days:
            date_str = day.strftime("%Y-%m-%d")
            print(
                f"\n===== 📆 Day {trading_days.index(day) + 1}/{len(trading_days)}: {date_str} ====="
            )
            if market_type == "stock":
                self.system.run_cycle(date_str)
            else:
                self.system.run_cycle()

        return self._collect_results()

    def _get_trading_days(self) -> List[datetime]:
        days: List[datetime] = []
        current = self.start_date
        while current <= self.end_date:
            if current.weekday() < 5:
                days.append(current)
            current += timedelta(days=1)
        return days

    def _collect_results(self) -> Dict[str, Any]:
        final_results = {}
        for agent_name, account in self.system.accounts.items():
            initial_cash = account.initial_cash
            final_value = account.get_total_value()
            return_pct = (
                ((final_value - initial_cash) / initial_cash) * 100
                if initial_cash > 0
                else 0
            )

            final_results[agent_name] = {
                "initial_value": initial_cash,
                "final_value": final_value,
                "return_percentage": return_pct,
                "period": f"{self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}",
            }
        return final_results


def run_backtest(
    models: List[tuple[str, str]],
    initial_cash: float,
    start_date: str,
    end_date: str,
    market_type: str = "stock",
) -> Dict[str, Any]:
    system: StockPortfolioSystem | PolymarketPortfolioSystem
    if market_type == "stock":
        system = StockPortfolioSystem()
    else:
        system = PolymarketPortfolioSystem()

    for name, model_id in models:
        system.add_agent(name=name, initial_cash=initial_cash, model_name=model_id)

    runner = BacktestRunner(system, start_date, end_date)
    return runner.run()

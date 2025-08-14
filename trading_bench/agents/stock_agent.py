from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from ..accounts import StockAccount, StockAction, create_stock_account
from .base_agent import BaseAgent


# ---------------------- Agent ----------------------
class LLMStockAgent(BaseAgent[StockAction, StockAccount, Dict[str, Any]]):
    """Symmetric, slim stock agent using the shared base."""

    def __init__(self, name: str, model_name: str = "gpt-4o-mini") -> None:
        super().__init__(name, model_name)

    # --- hooks ---
    def _extract_id_price(self, data: Dict[str, Any]) -> Tuple[str, float]:
        # New uniform keys:
        if "id" in data and "price" in data:
            return data["id"], float(data["price"])
        # Backward compat:
        return data["ticker"], float(data["current_price"])

    def _prepare_analysis_data(self, _id: str, price: float, data: Dict[str, Any], account: StockAccount) -> str:
        hist = self.history_tail(_id, 5)
        prev = self.prev_price(_id)
        pct = 0.0 if prev is None else ((price - prev) / prev) * 100.0
        trend = "increasing" if pct > 0 else ("decreasing" if pct < 0 else "stable")

        pos = account.get_active_positions().get(_id)
        pos_txt = f"holding {pos.quantity} @ ${pos.avg_price:.2f}" if pos else "no position"

        return (
            f"Stock Analysis:\n"
            f"- Ticker: {_id}\n"
            f"- Current: ${price:.2f}\n"
            f"- Change: {pct:+.2f}% ({trend})\n"
            f"- History: {[f'${p:.2f}' for p in hist]}\n"
            f"- Cash: ${account.cash_balance:.2f}\n"
            f"- Position: {pos_txt}\n\n"
            f"Decide buy/sell/hold with quantity (1-10) and reasoning."
        )

    def _create_action_from_response(self, parsed_response: Dict[str, Any], ticker: str, current_price: float) -> Optional[StockAction]:
        action = (parsed_response.get("action") or "hold").lower()
        if action == "hold":
            return None
        qty = int(parsed_response.get("quantity", 1))
        if qty <= 0:
            return None
        return StockAction(
            ticker=ticker,
            action=action,
            timestamp=datetime.now().isoformat(),
            price=current_price,
            quantity=qty,
        )

    def _get_system_prompt(self, analysis_data: str) -> List[Dict[str, str]]:
        sys = (
            "You are a professional stock trading agent.\n"
            "Return VALID JSON ONLY (no extra text).\n\n"
            "Format:\n"
            "{\n"
            '  "action": "buy" | "sell" | "hold",\n'
            '  "quantity": <int>,\n'
            '  "confidence": <0.0-1.0>,\n'
            '  "reasoning": "<brief>"\n'
            "}\n\n"
            "Rules: trade only if confidence>0.6, quantity 1-10, prefer smaller sizes."
        )
        return [
            {"role": "system", "content": sys},
            {"role": "user", "content": analysis_data},
        ]


# ---------------------- System ----------------------
class StockTradingSystem:
    """Symmetric trading loop for stocks."""

    def __init__(self, universe_size: int = 10) -> None:
        self.agents: Dict[str, LLMStockAgent] = {}
        self.accounts: Dict[str, StockAccount] = {}
        self.universe: List[str] = []
        self.iteration = 0
        self._initialize_universe(universe_size)

    def _initialize_universe(self, limit: int) -> None:
        try:
            from ..fetchers.stock_fetcher import fetch_trending_stocks
            stocks = fetch_trending_stocks(limit=limit)
            self.universe = [s["ticker"] for s in stocks]
            print(f"📊 Initialized {len(self.universe)} tickers: {', '.join(self.universe[:5])}...")
        except Exception as e:
            raise ValueError(f"Failed to fetch trending stocks: {e}")

    def add_agent(self, name: str, initial_cash: float = 1_000.0, model_name: str = "gpt-4o-mini") -> None:
        agent = LLMStockAgent(name, model_name)
        self.agents[name] = agent
        self.accounts[name] = create_stock_account(initial_cash)
        print(f"✅ Added agent {name} with ${initial_cash:.2f}")

    def _fetch_prices(self) -> Dict[str, float]:
        try:
            from ..fetchers.stock_fetcher import fetch_current_stock_price
            out: Dict[str, float] = {}
            for t in self.universe:
                p = fetch_current_stock_price(t)
                if p is not None:
                    out[t] = float(p)
            if out:
                return out
        except Exception as e:
            print(f"⚠️ Price fetch error: {e}")
            raise e

    def run_cycle(self) -> None:
        self.iteration += 1
        print(f"\n{'='*50}\n🔄 Stock Cycle {self.iteration}")

        try:
            prices = self._fetch_prices()
            if not prices:
                print("❌ No price data; skipping.")
                return

            preview = " | ".join(f"{t}: ${p:.2f}" for t, p in list(prices.items())[:5])
            print(f"📈 Prices: {preview}...")

            for agent_name, agent in self.agents.items():
                account = self.accounts[agent_name]
                print(f"\n🤖 {agent.name}:")
                for _id, price in prices.items():
                    data = {"id": _id, "price": price}  # uniform shape
                    action = agent.generate_action(data, account)
                    if action:
                        tag = f"{action.action.upper()} {action.quantity} {_id} @ ${action.price:.2f}"
                        print(f"   📊 {tag}")
                        ok, msg, _ = account.execute_action(action)
                        print(f"   {'✅' if ok else '❌'} {msg}")

                summary = account.evaluate()["portfolio_summary"]
                print(f"   💰 Cash: ${account.cash_balance:.2f}")
                print(f"   📈 Total Value: ${summary['total_value']:.2f}")

        except Exception as e:
            print(f"❌ Error in stock cycle: {e}")
            import traceback; traceback.print_exc()

    def run(self, duration_minutes: int = 10, interval: int = 60):
        """
        Run the trading system for a specified duration
        
        Args:
            duration_minutes: Total time to run the system in minutes
            interval: Seconds to wait between cycles (default: 60)
        """
        print(f"🚀 Starting stock trading system for {duration_minutes} minutes...")
        print(f"   Interval: {interval} seconds between cycles")
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        print(f"   Start: {start_time.strftime('%H:%M:%S')}")
        print(f"   End:   {end_time.strftime('%H:%M:%S')}")
        
        try:
            while datetime.now() < end_time:
                self.run_cycle()
                
                # Check if we should continue
                remaining = end_time - datetime.now()
                if remaining.total_seconds() <= 0:
                    break
                    
                # Wait before next cycle (user-configurable interval)
                print(f"⏱️  Waiting {interval}s... ({remaining.total_seconds()//60:.0f}m {remaining.total_seconds()%60:.0f}s remaining)")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n⏹️  Trading stopped by user")
        except Exception as e:
            print(f"\n❌ Trading system error: {e}")
            
        elapsed = datetime.now() - start_time
        print(f"\n✅ Trading completed! Ran for {elapsed.total_seconds()/60:.1f} minutes")

def create_stock_agent(name: str, model_name: str = "gpt-4o-mini") -> LLMStockAgent:
    return LLMStockAgent(name, model_name)

# Convenience
def create_trading_system() -> StockTradingSystem:
    return StockTradingSystem()

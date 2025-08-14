from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from ..accounts import PolymarketAccount, PolymarketAction, create_polymarket_account
from .base_agent import BaseAgent


# ---------------------- Agent ----------------------
class LLMPolyMarketAgent(BaseAgent[PolymarketAction, PolymarketAccount, Dict[str, Any]]):
    """Symmetric, slim Polymarket agent using the shared base."""

    def __init__(self, name: str, model_name: str = "gpt-4o-mini") -> None:
        super().__init__(name, model_name)

    # --- presentation tweak ---
    def _fmt_price(self, price: float) -> str:
        return f"{price:.2f}"  # probability display

    # --- hooks ---
    def _extract_id_price(self, data: Dict[str, Any]) -> Tuple[str, float]:
        # New uniform keys:
        if "id" in data and "price" in data:
            return data["id"], float(data["price"])
        # Backward compat:
        return data["market_id"], float(data["price"])

    def _prepare_analysis_data(self, _id: str, price: float, data: Dict[str, Any], account: PolymarketAccount) -> str:
        hist = [f"{p:.2f}" for p in self.history_tail(_id, 5)]
        prev = self.prev_price(_id)
        pct = 0.0 if prev is None else ((price - prev) / prev) * 100.0
        trend = "increasing" if pct > 0 else ("decreasing" if pct < 0 else "stable")

        yes_key = f"{_id}_yes"
        no_key = f"{_id}_no"
        pos = account.get_active_positions()
        pos_txt = []
        if yes_key in pos:
            pos_txt.append(f"YES {pos[yes_key].quantity}")
        if no_key in pos:
            pos_txt.append(f"NO {pos[no_key].quantity}")
        holdings = ", ".join(pos_txt) if pos_txt else "no positions"

        no_price = 1.0 - price

        return (
            "Prediction Market Analysis:\n"
            f"- Market: {_id}\n"
            f"- YES: {price:.3f} | NO: {no_price:.3f}\n"
            f"- Change: {pct:+.2f}% ({trend})\n"
            f"- History(YES): {hist}\n"
            f"- Cash: ${account.cash_balance:.2f}\n"
            f"- Positions: {holdings}\n\n"
            "Decide buy/sell/hold with outcome (yes/no), quantity (1-20), and reasoning."
        )

    def _create_action_from_response(self, parsed: Dict[str, Any], _id: str, price: float) -> Optional[PolymarketAction]:
        action = (parsed.get("action") or "hold").lower()
        if action == "hold":
            return None
        outcome = (parsed.get("outcome") or "yes").lower()
        qty = int(parsed.get("quantity", 10))
        conf = float(parsed.get("confidence", 0.5))
        if qty <= 0:
            return None
        return PolymarketAction(
            market_id=_id,
            outcome=outcome,
            action=action,
            timestamp=datetime.now().isoformat(),
            price=price,
            quantity=qty,
            confidence=conf,
        )

    def _get_system_prompt(self, analysis_data: str) -> List[Dict[str, str]]:
        sys = (
            "You are a professional prediction-market trading agent.\n"
            "Return VALID JSON ONLY (no extra text).\n\n"
            "Format:\n"
            "{\n"
            '  "action": "buy" | "sell" | "hold",\n'
            '  "outcome": "yes" | "no",\n'
            '  "quantity": <int>,\n'
            '  "confidence": <0.0-1.0>,\n'
            '  "reasoning": "<brief>"\n'
            "}\n\n"
            "Rules: trade only if confidence>0.6, quantity 1-20, prefer smaller sizes."
        )
        return [
            {"role": "system", "content": sys},
            {"role": "user", "content": analysis_data},
        ]


# ---------------------- System ----------------------
class PolymarketTradingSystem:
    """Symmetric trading loop for Polymarket."""

    def __init__(self, universe_size: int = 5) -> None:
        self.agents: Dict[str, LLMPolyMarketAgent] = {}
        self.accounts: Dict[str, PolymarketAccount] = {}
        self.universe: List[str] = []  # list of market_ids
        self.iteration = 0
        self._initialize_universe(universe_size)

    def _initialize_universe(self, limit: int) -> None:
        try:
            from ..fetchers.polymarket_fetcher import fetch_trending_markets
            markets = fetch_trending_markets(limit=limit)
            self.universe = [m["id"] for m in markets]
            print(f"📊 Initialized {len(self.universe)} markets: " +
                  " | ".join([m[:8] + "..." for m in self.universe[:3]]))
        except Exception as e:
            raise ValueError(f"Failed to fetch trending markets: {e}")

    def add_agent(self, name: str, initial_cash: float = 500.0, model_name: str = "gpt-4o-mini") -> None:
        agent = LLMPolyMarketAgent(name, model_name)
        self.agents[name] = agent
        self.accounts[name] = create_polymarket_account(initial_cash)
        print(f"✅ Added agent {name} with ${initial_cash:.2f}")

    def _fetch_prices(self) -> Dict[str, float]:
        try:
            from ..fetchers.polymarket_fetcher import fetch_current_market_price
            out: Dict[str, float] = {}
            for m in self.universe:
                prices = fetch_current_market_price(m)
                if prices and "yes" in prices:
                    out[m] = float(prices["yes"])
            if out:
                return out
        except Exception as e:
            print(f"⚠️ Price fetch error: {e}")

        # Fallback: simple themed defaults
        fb: Dict[str, float] = {}
        for m in self.universe:
            if "election" in m:
                fb[m] = 0.52
            elif "agi" in m:
                fb[m] = 0.25
            elif "climate" in m:
                fb[m] = 0.30
            else:
                fb[m] = 0.60
        return fb

    def run_cycle(self) -> None:
        self.iteration += 1
        print(f"\n{'='*50}\n🔮 Polymarket Cycle {self.iteration}")

        try:
            prices = self._fetch_prices()
            if not prices:
                print("❌ No market data; skipping.")
                return

            preview = " | ".join(f"{m[:8]}...: {p:.2f}" for m, p in list(prices.items())[:5])
            print(f"📈 Markets: {preview}...")

            for agent_name, agent in self.agents.items():
                account = self.accounts[agent_name]
                print(f"\n🤖 {agent.name}:")
                for _id, price in prices.items():
                    data = {"id": _id, "price": price}  # uniform shape
                    action = agent.generate_action(data, account)
                    if action:
                        tag = f"{action.action.upper()} {action.quantity} {action.outcome.upper()} @ {action.price:.2f}"
                        print(f"   📊 {tag}")
                        ok, msg, _ = account.execute_action(action)
                        print(f"   {'✅' if ok else '❌'} {msg}")

                summary = account.evaluate()["portfolio_summary"]
                print(f"   💰 Cash: ${account.cash_balance:.2f}")
                print(f"   📈 Total Value: ${summary['total_value']:.2f}")

        except Exception as e:
            print(f"❌ Error in polymarket cycle: {e}")
            import traceback; traceback.print_exc()

    def run(self, duration_minutes: int = 10, interval: int = 60):
        """
        Run the prediction market trading system for a specified duration
        
        Args:
            duration_minutes: Total time to run the system in minutes
            interval: Seconds to wait between cycles (default: 60)
        """
        print(f"🔮 Starting polymarket trading system for {duration_minutes} minutes...")
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

def create_polymarket_agent(name: str, model_name: str = "gpt-4o-mini") -> LLMPolyMarketAgent:
    return LLMPolyMarketAgent(name, model_name)

# Convenience
def create_polymarket_trading_system() -> PolymarketTradingSystem:
    return PolymarketTradingSystem()

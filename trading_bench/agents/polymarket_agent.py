"""
AI Prediction Market Agent for live trading simulation
"""

import time
from datetime import datetime
from typing import Dict, List, Optional

from ..accounts import PolymarketAccount, PolymarketAction, create_polymarket_account
from .base_agent import BaseAgent


class LLMPolyMarketAgent(BaseAgent[PolymarketAction, PolymarketAccount, Dict]):
    """AI-powered agent for prediction market trading"""

    def __init__(self, name: str, model_name: str = "gpt-4o-mini"):
        super().__init__(name, model_name)
        self.market_history: Dict[str, List[Dict]] = {}

    def generate_action(
        self, market_data: Dict, account: PolymarketAccount
    ) -> Optional[PolymarketAction]:
        """Generate PolymarketAction using LLM analysis"""
        market_id = market_data.get("id", "unknown")
        self._update_history(market_id, market_data)

        if not self.available:
            return None

        try:
            analysis_data = self._prepare_analysis_data(market_data, account)
            messages = [
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": analysis_data},
            ]

            llm_response = self._call_llm(messages)
            decision = self._parse_llm_response(llm_response)

            if not decision:
                return None

            action_type = decision.get("action", "hold").lower()
            outcome = decision.get("outcome", "yes").lower()
            quantity = decision.get("quantity", 10)
            confidence = decision.get("confidence", 0.5)

            price = self._calculate_price(market_data, outcome, confidence)

            # Validate and adjust
            if action_type == "buy":
                quantity = self._validate_buy(account, market_id, price, quantity)
            elif action_type == "sell":
                quantity = self._validate_sell(account, market_id, outcome, quantity)

            if action_type in ["buy", "sell"] and quantity > 0:
                return PolymarketAction(
                    market_id=market_id,
                    outcome=outcome,
                    action=action_type,
                    timestamp=datetime.now().isoformat(),
                    price=price,
                    quantity=quantity,
                    confidence=confidence,
                )
            return None

        except Exception as e:
            self._log_error(f"LLM error: {e}", market_id)
            return None

    def _update_history(self, market_id: str, market_data: Dict):
        """Update market history"""
        if market_id not in self.market_history:
            self.market_history[market_id] = []
        self.market_history[market_id].append(
            {"timestamp": datetime.now().isoformat(), "data": market_data}
        )
        if len(self.market_history[market_id]) > 5:
            self.market_history[market_id] = self.market_history[market_id][-5:]

    def _calculate_price(
        self, market_data: Dict, outcome: str, confidence: float
    ) -> float:
        """Calculate price based on market data and confidence"""
        market_price = self._get_current_market_price(market_data, outcome)
        if market_price is not None:
            adjustment = (confidence - 0.5) * 0.1
            price = market_price + adjustment
        else:
            price = confidence if outcome == "yes" else 1 - confidence
        return min(0.95, max(0.05, price))

    def _validate_buy(
        self, account: PolymarketAccount, market_id: str, price: float, quantity: int
    ) -> int:
        """Validate and adjust buy quantity"""
        can_afford, _ = account.can_afford(market_id, price, quantity)
        if not can_afford:
            for try_qty in [5, 3, 1]:
                can_afford, _ = account.can_afford(market_id, price, try_qty)
                if can_afford:
                    self._log_action(
                        f"Adjusted {market_id} quantity to {try_qty} shares"
                    )
                    return try_qty
            self._log_error("Insufficient funds", market_id)
            return 0
        return quantity

    def _validate_sell(
        self, account: PolymarketAccount, market_id: str, outcome: str, quantity: int
    ) -> int:
        """Validate and adjust sell quantity"""
        can_sell, _ = account.can_sell(market_id, outcome, quantity)
        if not can_sell:
            positions = account.get_active_positions()
            position_key = f"{market_id}_{outcome}"
            if position_key in positions and positions[position_key].quantity > 0:
                available = positions[position_key].quantity
                self._log_action(f"Selling all {available} available shares")
                return available
            else:
                self._log_error("No position to sell", f"{market_id} {outcome}")
                return 0
        return quantity

    def _get_current_market_price(
        self, market_data: Dict, outcome: str
    ) -> Optional[float]:
        """Get current market price for outcome"""
        outcomes = market_data.get("outcomes", [])
        for o in outcomes:
            if o.get("outcome") == outcome:
                return o.get("price")
        return None

    def _prepare_analysis_data(
        self, market_data: Dict, account: PolymarketAccount
    ) -> str:
        """Prepare analysis data for LLM"""
        market_id = market_data.get("id", "unknown")
        title = market_data.get("title", "Unknown market")
        category = market_data.get("category", "general")

        # Get prices
        outcomes = market_data.get("outcomes", [])
        yes_price = next(
            (o["price"] for o in outcomes if o.get("outcome") == "yes"), 0.5
        )
        no_price = next((o["price"] for o in outcomes if o.get("outcome") == "no"), 0.5)

        # Get position info
        positions = account.get_active_positions()
        position_key_yes = f"{market_id}_yes"
        position_key_no = f"{market_id}_no"
        current_yes = positions.get(position_key_yes)
        current_no = positions.get(position_key_no)

        position_info = []
        if current_yes:
            position_info.append(f"YES: {current_yes.quantity} shares")
        if current_no:
            position_info.append(f"NO: {current_no.quantity} shares")
        position_text = (
            ", ".join(position_info) if position_info else "No current positions"
        )

        return f"""
Market Analysis Request:
- ID: {market_id}
- Title: {title}
- Category: {category}
- YES Price: ${yes_price:.3f}
- NO Price: ${no_price:.3f}
- Account Balance: ${account.cash_balance:.2f}
- Current Positions: {position_text}

Please analyze and provide a trading decision (buy/sell/hold) with outcome (yes/no), quantity, and reasoning.
"""

    def _get_system_prompt(self) -> str:
        """Get the system prompt for prediction market decisions"""
        return """You are a professional prediction market trader. Analyze markets and make trading decisions.

Response format (JSON):
{
    "action": "buy|sell|hold",
    "outcome": "yes|no",
    "quantity": 10,
    "confidence": 0.7,
    "reasoning": "Brief explanation"
}

Guidelines:
- Only trade if you have strong conviction
- Consider market prices vs your assessment
- Manage risk with smaller position sizes
- Provide clear reasoning for decisions"""


class PolymarketTradingSystem:
    """Simplified polymarket trading system"""

    def __init__(self):
        self.agents: List[LLMPolyMarketAgent] = []
        self.accounts: Dict[str, PolymarketAccount] = {}
        self.iteration = 0
        self.start_time = datetime.now()
        self.markets: List[Dict] = []

        # Initialize: Fetch popular markets
        self._initialize_markets()

    def _initialize_markets(self):
        """Initialize by fetching popular/trending markets"""
        try:
            from ..fetchers.polymarket_fetcher import fetch_trending_markets

            markets = fetch_trending_markets(limit=5)
            self.markets = markets
            market_titles = [m["title"][:30] + "..." for m in markets[:3]]
            print(f"📊 Initialized with {len(self.markets)} trending markets:")
            for title in market_titles:
                print(f"  - {title}")
        except Exception as e:
            raise ValueError(f"Failed to fetch trending markets: {e}")

    def add_agent(
        self, name: str, initial_cash: float = 500.0, model_name: str = "gpt-4o-mini"
    ):
        """Add an AI prediction market agent"""
        agent = LLMPolyMarketAgent(name, model_name)
        account = create_polymarket_account(initial_cash, 0.02)
        self.agents.append(agent)
        self.accounts[name] = account
        print(f"✅ Added agent {name} with ${initial_cash:.2f}")

    def fetch_current_prices(self, markets: List[Dict]) -> Dict[str, Dict[str, float]]:
        """Iteratively fetch current prices for markets"""
        try:
            from ..fetchers.polymarket_fetcher import fetch_current_market_price

            market_prices = {}
            for market in markets:
                market_id = market["id"]
                prices = fetch_current_market_price(market_id)
                if prices:
                    market_prices[market_id] = prices
            if market_prices:
                return market_prices
        except Exception as e:
            print(f"⚠️ Price fetch error: {e}")

        # Fallback prices if no data fetched
        fallback_prices = {}
        for market in markets:
            market_id = market["id"]
            if "election" in market_id:
                fallback_prices[market_id] = {"yes": 0.52, "no": 0.48}
            elif "agi" in market_id:
                fallback_prices[market_id] = {"yes": 0.25, "no": 0.75}
            elif "climate" in market_id:
                fallback_prices[market_id] = {"yes": 0.30, "no": 0.70}
            else:
                fallback_prices[market_id] = {"yes": 0.50, "no": 0.50}
        return fallback_prices

    def run_cycle(self):
        """Run one trading cycle using initialized markets"""
        self.iteration += 1
        print(f"\n🔄 Cycle #{self.iteration} - {datetime.now().strftime('%H:%M:%S')}")

        if not self.markets:
            print("❌ No markets available")
            return

        # Fetch current prices for our initialized markets
        market_prices = self.fetch_current_prices(self.markets)
        if not market_prices:
            print("❌ No price data available")
            return

        # Show current prices
        price_info = []
        for market in self.markets[:3]:
            market_id = market["id"]
            if market_id in market_prices:
                yes_price = market_prices[market_id].get("yes", 0.5)
                price_info.append(f"{market_id}: {yes_price:.2f}")
        print(f"🎯 Current Prices: {' | '.join(price_info)}...")

        for agent in self.agents:
            account = self.accounts[agent.name]
            print(f"\n🤖 {agent.name}:")

            actions = 0
            for market in self.markets:
                market_id = market["id"]
                if market_id in market_prices:
                    # Add current prices to market data
                    market_with_prices = market.copy()
                    market_with_prices["outcomes"] = [
                        {"outcome": "yes", "price": market_prices[market_id]["yes"]},
                        {"outcome": "no", "price": market_prices[market_id]["no"]},
                    ]

                    action = agent.generate_action(market_with_prices, account)
                    if action:
                        # Print the generated action
                        market_title = (
                            market["title"][:30] + "..."
                            if len(market["title"]) > 30
                            else market["title"]
                        )
                        price = (
                            market_prices[market_id][action.outcome]
                            if hasattr(action, "outcome")
                            else 0.5
                        )
                        print(
                            f"  🎯 {market_title}: {action.action.upper()} {action.quantity} {action.outcome.upper() if hasattr(action, 'outcome') else 'shares'} (${action.quantity * price:.2f})"
                        )
                        if action.action != "hold":
                            actions += 1

                        # Execute the action
                        if action.action != "hold":
                            success, message, _ = account.execute_action(action)
                            print(f"    {'✅' if success else '❌'} {message}")
                    else:
                        market_title = (
                            market["title"][:30] + "..."
                            if len(market["title"]) > 30
                            else market["title"]
                        )
                        print(f"  🎯 {market_title}: HOLD (no action generated)")

            print(
                f"  💼 Balance: ${account.cash_balance:.2f} | Portfolio: ${account.evaluate()['portfolio_summary']['total_value']:.2f} | Actions: {actions}"
            )

    def run(self, cycles: int = 3, interval: float = 2.0):
        """Run multiple trading cycles"""
        print(f"\n🚀 Starting PolymarketTradingSystem with {len(self.agents)} agents")
        print(f"📊 Trading on {len(self.markets)} markets")

        try:
            for cycle in range(cycles):
                self.run_cycle()
                if cycle < cycles - 1:
                    print(f"⏳ Waiting {interval}s...")
                    time.sleep(interval)
        except KeyboardInterrupt:
            print("\n⏹️ Trading stopped by user")


# Convenience functions
def create_polymarket_agent(
    name: str, model_name: str = "gpt-4o-mini"
) -> LLMPolyMarketAgent:
    """Create a new AI polymarket agent"""
    return LLMPolyMarketAgent(name, model_name)


def create_polymarket_trading_system() -> PolymarketTradingSystem:
    """Create a new polymarket trading system"""
    return PolymarketTradingSystem()

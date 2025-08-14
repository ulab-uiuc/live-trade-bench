"""
AI Trading Agent for live trading simulation
"""

import time
from datetime import datetime
from typing import Dict, List, Optional

from ..accounts import StockAccount, StockAction, create_stock_account
from .base_agent import BaseAgent


class LLMStockAgent(BaseAgent[StockAction, StockAccount, tuple]):
    """AI-powered trading agent that uses LLM for trading decisions"""

    def __init__(self, name: str, model_name: str = "gpt-4o-mini"):
        super().__init__(name, model_name)
        self.price_history: Dict[str, List[float]] = {}

    def generate_action(
        self, data: dict, account: StockAccount
    ) -> Optional[StockAction]:
        """Generate StockAction using LLM analysis"""
        # Extract data from dictionary format
        ticker = data["ticker"]
        current_price = data["current_price"]

        self._update_history(ticker, current_price)

        if not self.available:
            return None

        try:
            analysis_data = self._prepare_analysis_data(data, account)
            messages = [
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": analysis_data},
            ]

            llm_response = self._call_llm(messages)
            decision = self._parse_llm_response(llm_response)

            if not decision:
                return None

            action_type = decision.get("action", "hold").lower()
            quantity = decision.get("quantity", 1)

            # Validate and adjust quantity
            if action_type == "buy":
                quantity = self._validate_buy(account, ticker, current_price, quantity)
            elif action_type == "sell":
                quantity = self._validate_sell(account, ticker, quantity)

            if action_type in ["buy", "sell"] and quantity > 0:
                return StockAction(
                    ticker=ticker,
                    action=action_type,
                    timestamp=datetime.now().isoformat(),
                    price=current_price,
                    quantity=quantity,
                )
            return None

        except Exception as e:
            self._log_error(f"LLM error: {e}", ticker)
            return None

    def _update_history(self, ticker: str, price: float):
        """Update price history for a ticker"""
        if ticker not in self.price_history:
            self.price_history[ticker] = []
        self.price_history[ticker].append(price)
        if len(self.price_history[ticker]) > 10:
            self.price_history[ticker] = self.price_history[ticker][-10:]

    def _validate_buy(
        self, account: StockAccount, ticker: str, price: float, quantity: int
    ) -> int:
        """Validate and adjust buy quantity"""
        can_afford, _ = account.can_afford(ticker, price, quantity)
        if not can_afford:
            max_affordable = int(account.cash_balance // price)
            if max_affordable > 0:
                self._log_action(
                    f"Adjusted {ticker} to affordable quantity",
                    f"{max_affordable} shares",
                )
                return max_affordable
            else:
                self._log_error("Insufficient funds", ticker)
                return 0
        return quantity

    def _validate_sell(self, account: StockAccount, ticker: str, quantity: int) -> int:
        """Validate and adjust sell quantity"""
        can_sell, _ = account.can_sell(ticker, quantity)
        if not can_sell:
            positions = account.get_active_positions()
            if ticker in positions and positions[ticker].quantity > 0:
                available = positions[ticker].quantity
                self._log_action(
                    f"Selling all available shares of {ticker}", f"{available} shares"
                )
                return available
            else:
                self._log_error("No position to sell", ticker)
                return 0
        return quantity

    def _prepare_analysis_data(self, data: dict, account: StockAccount) -> str:
        """Prepare analysis data for LLM"""
        ticker = data["ticker"]
        current_price = data["current_price"]

        # Get price history
        history = self.price_history.get(ticker, [current_price])
        if len(history) >= 2:
            price_change = ((current_price - history[-2]) / history[-2]) * 100
            trend = "increasing" if price_change > 0 else "decreasing"
        else:
            price_change = 0
            trend = "stable"

        # Get account info
        positions = account.get_active_positions()
        current_position = positions.get(ticker)
        position_info = (
            f"Currently holding {current_position.quantity} shares at avg ${current_position.avg_price:.2f}"
            if current_position
            else "No current position"
        )

        return f"""
Stock Analysis Request:
- Ticker: {ticker}
- Current Price: ${current_price:.2f}
- Price Change: {price_change:+.2f}% ({trend})
- Price History: {[f"${p:.2f}" for p in history[-5:]]}
- Account Balance: ${account.cash_balance:.2f}
- {position_info}

Please analyze and provide a trading decision (buy/sell/hold) with quantity and reasoning.
"""

    def _get_system_prompt(self) -> str:
        """Get the system prompt for stock trading decisions"""
        return """You are a professional stock trader. Analyze the provided data and make trading decisions.

Response format (JSON):
{
    "action": "buy|sell|hold",
    "quantity": 1,
    "confidence": 0.7,
    "reasoning": "Brief explanation"
}

Guidelines:
- Only buy/sell if you have high confidence
- Consider price trends and account balance
- Default to smaller quantities for risk management
- Provide clear reasoning for decisions"""


class StockTradingSystem:
    """Simplified trading system for AI agents"""

    def __init__(self):
        self.agents: List[LLMStockAgent] = []
        self.accounts: Dict[str, StockAccount] = {}
        self.iteration = 0
        self.start_time = datetime.now()
        self.tickers: List[str] = []

        # Initialize: Fetch popular stocks
        self._initialize_stocks()

    def _initialize_stocks(self):
        """Initialize by fetching popular/trending stocks"""
        try:
            from ..fetchers.stock_fetcher import fetch_trending_stocks

            stocks = fetch_trending_stocks(limit=10)
            self.tickers = [stock["ticker"] for stock in stocks]
            print(
                f"📊 Initialized with {len(self.tickers)} trending stocks: {', '.join(self.tickers[:5])}..."
            )
        except Exception as e:
            raise ValueError(f"Failed to fetch trending stocks: {e}")

    def add_agent(
        self, name: str, initial_cash: float = 1000.0, model_name: str = "gpt-4o-mini"
    ):
        """Add an AI trading agent"""
        agent = LLMStockAgent(name, model_name)
        account = create_stock_account(initial_cash)
        self.agents.append(agent)
        self.accounts[name] = account
        print(f"✅ Added agent {name} with ${initial_cash:.2f}")

    def fetch_current_prices(self, tickers: List[str]) -> Dict[str, float]:
        """Iteratively fetch current prices for tickers"""
        try:
            from ..fetchers.stock_fetcher import fetch_current_stock_price

            prices = {}
            for ticker in tickers:
                price = fetch_current_stock_price(ticker)
                if price is not None:
                    prices[ticker] = price
            if prices:
                return prices
        except Exception as e:
            print(f"⚠️ Price fetch error: {e}")

        # Fallback prices if no data fetched
        defaults = {
            "AAPL": 180.0,
            "MSFT": 350.0,
            "GOOGL": 140.0,
            "AMZN": 150.0,
            "TSLA": 200.0,
            "META": 300.0,
            "NVDA": 450.0,
            "JPM": 160.0,
            "JNJ": 170.0,
            "V": 250.0,
        }
        return {t: defaults.get(t, 150.0) for t in tickers}

    def run_cycle(self):
        """Run one trading cycle using initialized tickers"""
        self.iteration += 1
        print(f"\n🔄 Cycle #{self.iteration} - {datetime.now().strftime('%H:%M:%S')}")

        # Fetch current prices for our initialized stocks
        prices = self.fetch_current_prices(self.tickers)
        if not prices:
            print("❌ No price data available")
            return

        # Show current prices
        price_info = [
            f"{ticker}: ${price:.2f}" for ticker, price in list(prices.items())[:3]
        ]
        print(f"📈 Current Prices: {' | '.join(price_info)}...")

        for agent in self.agents:
            account = self.accounts[agent.name]
            print(f"\n🤖 {agent.name}:")

            actions = 0
            for ticker in self.tickers:
                if ticker in prices:
                    # Create stock data for agent
                    stock_data = {
                        "ticker": ticker,
                        "current_price": prices[ticker],
                        "price_history": agent.price_history.get(ticker, []),
                    }

                    action = agent.generate_action(stock_data, account)
                    if action:
                        # Print the generated action
                        print(
                            f"  📊 {ticker}: {action.action.upper()} {action.quantity} shares (${action.quantity * prices[ticker]:.2f})"
                        )
                        if action.action != "hold":
                            actions += 1

                        # Execute the action
                        if action.action != "hold":
                            success, message, _ = account.execute_action(action)
                            print(f"    {'✅' if success else '❌'} {message}")
                    else:
                        print(f"  📊 {ticker}: HOLD (no action generated)")

                    # Update price history
                    agent._update_history(ticker, prices[ticker])

            print(
                f"  💼 Balance: ${account.cash_balance:.2f} | Portfolio: ${account.evaluate()['portfolio_summary']['total_value']:.2f} | Actions: {actions}"
            )

    def run(self, cycles: int = 3, interval: float = 2.0):
        """Run multiple trading cycles"""
        print(f"\n🚀 Starting TradingSystem with {len(self.agents)} agents")
        print(f"📊 Trading on {len(self.tickers)} stocks")

        try:
            for cycle in range(cycles):
                self.run_cycle()
                if cycle < cycles - 1:
                    print(f"⏳ Waiting {interval}s...")
                    time.sleep(interval)
        except KeyboardInterrupt:
            print("\n⏹️ Trading stopped by user")


def create_trading_system() -> StockTradingSystem:
    """Create a new trading system"""
    return StockTradingSystem()

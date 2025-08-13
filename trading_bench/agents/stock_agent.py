"""
AI Trading Agent for live trading simulation
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from ..evaluators import StockAccount, StockAction, create_stock_account


class AITradingAgent:
    """AI-powered trading agent that uses LLM for trading decisions"""

    def __init__(self, name: str, model_name: str = "gpt-4o-mini"):
        self.name = name
        self.model_name = model_name
        self.price_history: Dict[str, List[float]] = {}

        # Check if LLM is available
        try:
            from ..utils import call_llm

            self.available = True
            print(f"🤖 {name}: LLM enabled with {model_name}")
        except ImportError:
            self.available = False
            print(f"⚠️ {name}: LLM utils not available")

    def update_price_history(self, ticker: str, price: float):
        """Update price history for a ticker"""
        if ticker not in self.price_history:
            self.price_history[ticker] = []

        self.price_history[ticker].append(price)
        # Keep only last 10 prices
        if len(self.price_history[ticker]) > 10:
            self.price_history[ticker] = self.price_history[ticker][-10:]

    def generate_action(
        self, ticker: str, current_price: float, account: StockAccount
    ) -> Optional[StockAction]:
        """Generate StockAction using LLM analysis"""
        self.update_price_history(ticker, current_price)

        if not self.available:
            print(f"⚠️ {self.name}: LLM not available for {ticker}")
            return None

        try:
            from ..utils import call_llm, parse_trading_response

            # Prepare data for LLM
            analysis_data = self._prepare_analysis_data(ticker, current_price, account)

            # Get LLM decision
            messages = [
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": analysis_data},
            ]

            llm_response = call_llm(messages, self.model_name, self.name)

            if llm_response["success"]:
                decision = parse_trading_response(llm_response["content"])
            else:
                print(f"⚠️ {self.name}: {llm_response['error']} for {ticker}")
                return None

            action_type = decision.get("action", "hold").lower()
            quantity = decision.get("quantity", 1)
            reasoning = decision.get("reasoning", "LLM decision")

            # Validate the decision
            if action_type == "buy":
                can_afford, _ = account.can_afford(ticker, current_price, quantity)
                if not can_afford:
                    # Try with 1 share
                    can_afford, _ = account.can_afford(ticker, current_price, 1)
                    if can_afford:
                        quantity = 1
                    else:
                        # Try fractional shares - buy what we can afford
                        max_affordable = int(account.cash_balance // current_price)
                        if max_affordable > 0:
                            quantity = max_affordable
                            print(
                                f"💡 {self.name}: Adjusted {ticker} to affordable quantity: {quantity} shares"
                            )
                        else:
                            print(
                                f"⚠️ {self.name}: Insufficient funds for {ticker} (${account.cash_balance:.2f} < ${current_price:.2f})"
                            )
                            return None

            elif action_type == "sell":
                can_sell, _ = account.can_sell(ticker, quantity)
                if not can_sell:
                    # Try to sell available shares
                    positions = account.get_active_positions()
                    if ticker in positions and positions[ticker].quantity > 0:
                        quantity = positions[ticker].quantity
                    else:
                        print(f"⚠️ {self.name}: No position to sell for {ticker}")
                        return None

            # Create StockAction if valid
            if action_type in ["buy", "sell"] and quantity > 0:
                return StockAction(
                    ticker=ticker,
                    action=action_type,
                    timestamp=datetime.now().isoformat(),
                    price=current_price,
                    quantity=quantity,
                )

            return None  # Hold action

        except Exception as e:
            print(f"⚠️ {self.name}: LLM error for {ticker}: {e}")
            return None

    def _prepare_analysis_data(
        self, ticker: str, current_price: float, account: StockAccount
    ) -> str:
        """Prepare analysis data for LLM"""
        prices = self.price_history.get(ticker, [])

        # Calculate basic indicators
        if len(prices) >= 2:
            price_change = current_price - prices[-1]
            price_change_pct = (price_change / prices[-1]) * 100
        else:
            price_change = 0
            price_change_pct = 0

        # Moving averages
        ma_3 = sum(prices[-3:]) / min(3, len(prices)) if prices else current_price
        ma_5 = sum(prices[-5:]) / min(5, len(prices)) if prices else current_price

        # Account info
        portfolio_summary = account.evaluate()["portfolio_summary"]
        active_positions = account.get_active_positions()
        current_position = active_positions.get(ticker)

        # Portfolio diversification info
        total_positions = len(active_positions)
        portfolio_tickers = list(active_positions.keys())

        analysis_prompt = f"""
Stock Analysis for {ticker}:

Current Price: ${current_price:.2f}
Price Change: ${price_change:.2f} ({price_change_pct:.2f}%)
3-day MA: ${ma_3:.2f}
5-day MA: ${ma_5:.2f}
Recent Prices: {prices[-5:] if len(prices) >= 5 else prices}

Account Information:
- Cash Balance: ${account.cash_balance:.2f}
- Total Portfolio Value: ${portfolio_summary['total_value']:.2f}
- Portfolio Return: {portfolio_summary['return_pct']:.1f}%
- Current Position in {ticker}: {current_position.quantity if current_position else 0} shares
- Total Positions: {total_positions} stocks
- Portfolio: {portfolio_tickers if portfolio_tickers else "No positions"}

Market Conditions:
- Price vs 3-day MA: {'Above' if current_price > ma_3 else 'Below'} by {abs(current_price - ma_3):.2f}
- Price vs 5-day MA: {'Above' if current_price > ma_5 else 'Below'} by {abs(current_price - ma_5):.2f}

Diversification Context:
Consider portfolio diversification and risk management across multiple stocks.
Current portfolio concentration and available cash for new positions.

Based on this analysis, should I buy, sell, or hold {ticker}?
Consider technical indicators, account balance, current position, and portfolio diversification.
"""
        return analysis_prompt

    def _get_system_prompt(self) -> str:
        """Get the system prompt for trading decisions"""
        return """You are a professional stock trader managing a diversified portfolio. Analyze the provided data and make a trading decision.

Rules:
- Only recommend BUY if there's sufficient cash and positive technical signals
- Only recommend SELL if there's existing position and negative signals
- Use HOLD when conditions are neutral or unclear
- Consider risk management - don't risk too much on one trade
- Consider portfolio diversification - avoid over-concentration in one stock
- Quantity should be 1-3 shares maximum for small accounts
- Factor in existing positions and available cash for diversification

Respond with JSON format:
{
    "action": "buy/sell/hold",
    "quantity": 1,
    "confidence": 0.7,
    "reasoning": "Brief explanation of decision including diversification considerations"
}"""


class TradingSystem:
    """Simple trading system for AI agents using real market data across multiple stocks"""

    def __init__(self):
        self.agents: List[AITradingAgent] = []
        self.accounts: Dict[str, StockAccount] = {}
        self.iteration = 0
        self.start_time = datetime.now()

        # Popular stocks to trade
        self.default_tickers = [
            "AAPL",  # Apple
            "MSFT",  # Microsoft
            "GOOGL",  # Google
            "AMZN",  # Amazon
            "TSLA",  # Tesla
            "META",  # Meta
            "NVDA",  # NVIDIA
            "NFLX",  # Netflix
            "CRM",  # Salesforce
            "UBER",  # Uber
        ]

    def _fetch_stock_data(
        self, ticker: str, days: int = 5
    ) -> Dict[str, Dict[str, float]]:
        """Fetch real stock data"""
        try:
            from ..fetchers.stock_fetcher import fetch_stock_data

            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            data = fetch_stock_data(
                ticker,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
                resolution="1",
            )

            return data if data else {}

        except Exception as e:
            print(f"⚠️ Failed to fetch data for {ticker}: {e}")
            return {}

    def _get_latest_price(self, ticker: str) -> Optional[float]:
        """Get the latest price for a ticker using improved fetcher"""
        try:
            # Use the new current price method from fetcher
            from ..fetchers.stock_fetcher import get_current_stock_price
            
            price = get_current_stock_price(ticker)
            if price and price > 0:
                return price
                
        except Exception as e:
            print(f"⚠️ Real-time price fetch failed for {ticker}: {e}")

        # Fallback: Use historical data method
        data = self._fetch_stock_data(ticker)
        if data:
            # Get the most recent date/time
            latest_key = max(data.keys())
            latest_data = data[latest_key]
            price = latest_data.get("close", latest_data.get("price", 0))
            if price > 0:
                return price

        default_prices = {
            "AAPL": 180.0,
            "MSFT": 350.0,
            "GOOGL": 140.0,
            "AMZN": 150.0,
            "TSLA": 200.0,
            "META": 300.0,
            "NVDA": 450.0,
            "NFLX": 400.0,
            "CRM": 220.0,
            "UBER": 60.0,
        }
        return default_prices.get(ticker, 150.0)

    def add_agent(
        self, name: str, initial_cash: float = 1000.0, model_name: str = "gpt-4o-mini"
    ):
        """Add an AI trading agent with its own account (increased default cash for multiple stocks)"""
        agent = AITradingAgent(name, model_name)
        account = create_stock_account(initial_cash)

        self.agents.append(agent)
        self.accounts[name] = account

        print(f"✅ Added AI agent {name} with ${initial_cash:.2f}")

    def run_cycle(self, tickers: List[str]):
        """Run one trading cycle across multiple stocks"""
        self.iteration += 1
        print(f"\n🔄 Cycle #{self.iteration} - {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 80)

        # Get current prices for all tickers
        current_prices = {}
        for ticker in tickers:
            price = self._get_latest_price(ticker)
            if price:
                current_prices[ticker] = price

        if not current_prices:
            print("❌ Could not fetch prices for any tickers, skipping cycle")
            return

        # Display current prices
        price_display = " | ".join(
            [f"{t}: ${p:.1f}" for t, p in current_prices.items()]
        )
        print(f"📈 Prices: {price_display}")

        # Each agent analyzes all stocks and may take action on any
        for agent in self.agents:
            account = self.accounts[agent.name]

            print(f"\n🤖 {agent.name}:")

            actions_taken = 0
            # Agent considers each stock
            for ticker in tickers:
                if ticker not in current_prices:
                    continue

                current_price = current_prices[ticker]

                # Agent generates StockAction (or None)
                stock_action = agent.generate_action(ticker, current_price, account)

                if stock_action:
                    print(
                        f"  {ticker}: {stock_action.action.upper()} {stock_action.quantity} shares"
                    )

                    # Account processes StockAction
                    success, message, transaction = account.execute_action(stock_action)

                    status = "✅" if success else "❌"
                    print(f"    Result: {status} {message}")

                    if success:
                        actions_taken += 1

            if actions_taken == 0:
                print("  No actions taken across all stocks")

            # Show account status
            try:
                evaluation = account.evaluate()
                total_value = evaluation["portfolio_summary"]["total_value"]
                return_pct = evaluation["portfolio_summary"]["return_pct"]

                print(f"  Portfolio: ${total_value:.2f} ({return_pct:+.1f}%)")
                print(f"  Cash: ${account.cash_balance:.2f}")

                active_positions = account.get_active_positions()
                if active_positions:
                    pos_str = ", ".join(
                        [f"{t}({p.quantity:.0f})" for t, p in active_positions.items()]
                    )
                    print(f"  Positions: {pos_str}")

            except Exception as e:
                print(f"  ⚠️ Evaluation failed: {e}")

    def print_summary(self):
        """Print system summary"""
        print("\n📊 Summary")
        print("=" * 60)

        total_initial = len(self.agents) * 1000.0  # Updated for new default
        total_current = 0.0

        for agent in self.agents:
            account = self.accounts[agent.name]

            try:
                evaluation = account.evaluate()
                total_value = evaluation["portfolio_summary"]["total_value"]
                return_pct = evaluation["portfolio_summary"]["return_pct"]
            except:
                total_value = account.cash_balance
                return_pct = (total_value - 1000.0) / 1000.0 * 100

            trades = len(account.transactions)
            total_current += total_value

            # Show positions
            active_positions = account.get_active_positions()
            pos_count = len(active_positions)

            print(
                f"{agent.name}: ${total_value:.2f} ({return_pct:+.1f}%) | {trades} trades | {pos_count} positions"
            )

        system_return = (
            ((total_current - total_initial) / total_initial * 100)
            if total_initial > 0
            else 0.0
        )
        runtime = datetime.now() - self.start_time

        print(
            f"Total: ${total_current:.2f} ({system_return:+.1f}%) | {runtime.total_seconds():.0f}s"
        )

    def run(self, tickers: List[str] = None, cycles: int = 5, interval: float = 2.0):
        """Run the AI trading system across multiple stocks"""
        if tickers is None:
            tickers = self.default_tickers

        print("🚀 AI Multi-Stock Trading System")
        print(f"📈 Stocks: {', '.join(tickers)}")
        print(f"🔄 Cycles: {cycles}")
        print(f"🤖 AI Agents: {len(self.agents)}")

        try:
            for cycle in range(cycles):
                self.run_cycle(tickers)
                self.print_summary()

                if cycle < cycles - 1:
                    print(f"\n⏳ Waiting {interval}s...")
                    time.sleep(interval)

        except KeyboardInterrupt:
            print("\n⏹️ Trading stopped by user")

        print("\n🏁 Trading completed!")
        self.print_summary()


def create_trading_system() -> TradingSystem:
    """Create a new AI trading system"""
    return TradingSystem()

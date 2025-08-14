"""
AI Prediction Market Agent for live trading simulation
"""

import time
from datetime import datetime
from typing import Dict, List, Optional

from ..accounts import PolymarketAccount, PolymarketAction, create_polymarket_account


class AIPolymarketAgent:
    """AI-powered agent for prediction market trading"""

    def __init__(self, name: str, model_name: str = "gpt-4o-mini"):
        self.name = name
        self.model_name = model_name
        self.market_history: Dict[str, List[Dict]] = {}

        # Check if LLM is available
        try:
            from ..utils import call_llm

            self.available = True
            print(f"🎯 {name}: LLM enabled for prediction market analysis")
        except ImportError:
            self.available = False
            print(f"⚠️ {name}: LLM utils not available")

    def update_market_history(self, market_id: str, market_data: Dict):
        """Update market history for analysis"""
        if market_id not in self.market_history:
            self.market_history[market_id] = []

        self.market_history[market_id].append(
            {"timestamp": datetime.now().isoformat(), "data": market_data}
        )

        # Keep only last 5 data points
        if len(self.market_history[market_id]) > 5:
            self.market_history[market_id] = self.market_history[market_id][-5:]

    def generate_action(
        self, market_data: Dict, account: PolymarketAccount
    ) -> Optional[PolymarketAction]:
        """Generate PolymarketAction using LLM analysis"""
        market_id = market_data.get("id", "unknown")
        self.update_market_history(market_id, market_data)

        if not self.available:
            print(f"⚠️ {self.name}: LLM not available for {market_id}")
            return None

        try:
            from ..utils import call_llm, parse_trading_response

            # Prepare analysis data for LLM
            analysis_data = self._prepare_market_analysis(market_data, account)

            # Get LLM decision
            messages = [
                {"role": "system", "content": self._get_prediction_prompt()},
                {"role": "user", "content": analysis_data},
            ]

            llm_response = call_llm(messages, self.model_name, self.name)

            if llm_response["success"]:
                decision = parse_trading_response(llm_response["content"])
            else:
                print(f"⚠️ {self.name}: {llm_response['error']} for {market_id}")
                return None

            # Parse decision for prediction markets
            action_type = decision.get("action", "hold").lower()
            outcome = decision.get("outcome", "yes").lower()  # Default to yes
            quantity = decision.get("quantity", 10)
            confidence = decision.get("confidence", 0.5)
            reasoning = decision.get("reasoning", "LLM decision")

            # Estimate price based on confidence and current market odds
            market_price = self._get_current_market_price(market_data, outcome)
            if market_price is not None:
                # Adjust price based on confidence
                if outcome == "yes":
                    price = min(
                        0.95, max(0.05, market_price + (confidence - 0.5) * 0.1)
                    )
                else:
                    price = min(
                        0.95, max(0.05, market_price + (confidence - 0.5) * 0.1)
                    )
            else:
                # Fallback to confidence-based pricing
                if outcome == "yes":
                    price = min(0.95, max(0.05, confidence))
                else:
                    price = min(0.95, max(0.05, 1 - confidence))

            # Validate the decision
            if action_type == "buy":
                can_afford, _ = account.can_afford(market_id, price, quantity)
                if not can_afford:
                    # Try with smaller quantities
                    for try_qty in [5, 3, 1]:
                        can_afford, _ = account.can_afford(market_id, price, try_qty)
                        if can_afford:
                            quantity = try_qty
                            print(
                                f"💡 {self.name}: Adjusted {market_id} quantity to {quantity} shares"
                            )
                            break
                    else:
                        print(
                            f"⚠️ {self.name}: Insufficient funds for {market_id} (${account.cash_balance:.2f} < ${price * quantity:.2f})"
                        )
                        return None

            elif action_type == "sell":
                can_sell, _ = account.can_sell(market_id, outcome, quantity)
                if not can_sell:
                    # Try to sell available shares
                    positions = account.get_active_positions()
                    position_key = f"{market_id}_{outcome}"
                    if (
                        position_key in positions
                        and positions[position_key].quantity > 0
                    ):
                        quantity = positions[position_key].quantity
                        print(
                            f"💡 {self.name}: Selling all {quantity} available shares of {market_id} {outcome}"
                        )
                    else:
                        print(
                            f"⚠️ {self.name}: No position to sell for {market_id} {outcome}"
                        )
                        return None

            # Create PolymarketAction if valid
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

            return None  # Hold action

        except Exception as e:
            print(f"⚠️ {self.name}: LLM error for {market_id}: {e}")
            return None

    def _get_current_market_price(
        self, market_data: Dict, outcome: str
    ) -> Optional[float]:
        """Get current market price for specific outcome"""
        outcomes = market_data.get("outcomes", [])
        for outcome_data in outcomes:
            if outcome_data.get("outcome", "").lower() == outcome.lower():
                return outcome_data.get("price")
        return None

    def _prepare_market_analysis(
        self, market_data: Dict, account: PolymarketAccount
    ) -> str:
        """Prepare market analysis data for LLM"""
        market_id = market_data.get("id", "unknown")
        title = market_data.get("title", "Unknown Market")
        category = market_data.get("category", "unknown")
        description = market_data.get("description", "No description")
        end_date = market_data.get("end_date", "Unknown")
        
        # Ensure volume and liquidity are not None
        volume = market_data.get("total_volume") or 0
        liquidity = market_data.get("total_liquidity") or 0
        
        # Convert to float if they're strings
        try:
            volume = float(volume) if volume is not None else 0.0
        except (ValueError, TypeError):
            volume = 0.0
            
        try:
            liquidity = float(liquidity) if liquidity is not None else 0.0
        except (ValueError, TypeError):
            liquidity = 0.0

        # Get current odds from outcomes
        yes_price = 0.5
        no_price = 0.5
        outcomes = market_data.get("outcomes", [])
        for outcome in outcomes:
            if outcome.get("outcome", "").lower() == "yes":
                price = outcome.get("price", 0.5)
                yes_price = float(price) if price is not None else 0.5
            elif outcome.get("outcome", "").lower() == "no":
                price = outcome.get("price", 0.5)
                no_price = float(price) if price is not None else 0.5

        # Account information
        portfolio_summary = account.evaluate()["portfolio_summary"]
        active_positions = account.get_active_positions()

        # Check if we have position in this market
        current_positions = {}
        for position_key, position in active_positions.items():
            if position.market_id == market_id:
                current_positions[position.outcome] = position

        # Historical data
        history = self.market_history.get(market_id, [])

        # Calculate time to resolution
        time_to_resolution = "Unknown"
        try:
            if end_date != "Unknown" and end_date:
                end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                now_dt = datetime.now()
                time_diff = end_dt - now_dt
                if time_diff.days > 0:
                    time_to_resolution = f"{time_diff.days} days"
                elif time_diff.seconds > 3600:
                    time_to_resolution = f"{time_diff.seconds // 3600} hours"
                else:
                    time_to_resolution = "Less than 1 hour"
        except:
            pass

        analysis_prompt = f"""
Prediction Market Analysis for: {title}

Market Details:
- Market ID: {market_id}
- Category: {category}
- Description: {description}
- Resolution Date: {end_date}
- Time to Resolution: {time_to_resolution}
- Trading Volume: ${volume:,.0f}
- Market Liquidity: ${liquidity:,.0f}

Current Market Odds:
- YES: ${yes_price:.3f} ({yes_price*100:.1f}% implied probability)
- NO: ${no_price:.3f} ({no_price*100:.1f}% implied probability)

Account Information:
- Cash Balance: ${account.cash_balance:.2f}
- Total Portfolio Value: ${portfolio_summary['total_value']:.2f}
- Portfolio Return: {portfolio_summary['return_pct']:.1f}%
- Active Positions: {len(active_positions)} markets

Current Positions in This Market:
{self._format_current_positions(current_positions)}

Market Activity Analysis:
- Data points collected: {len(history)}
- Historical analysis: {'Available' if len(history) > 1 else 'Limited'}

Risk Assessment:
- Market Liquidity: {'High' if liquidity > 50000 else 'Medium' if liquidity > 10000 else 'Low'}
- Trading Volume: {'High' if volume > 100000 else 'Medium' if volume > 20000 else 'Low'}
- Market Maturity: {'Mature' if volume > 50000 else 'Developing'}
- Resolution Timeline: {time_to_resolution}

Market Context by Category:
{self._get_category_context(category)}

Based on this comprehensive analysis, should I trade in this prediction market?
Consider:
1. Market fundamentals and liquidity
2. Current odds vs your assessment
3. Time to resolution
4. Portfolio diversification
5. Risk/reward ratio
"""
        return analysis_prompt

    def _format_current_positions(self, positions: Dict) -> str:
        """Format current positions for display"""
        if not positions:
            return "- No current positions in this market"

        formatted = []
        for outcome, position in positions.items():
            pnl_estimate = (
                0.5 - position.avg_price
            ) * position.quantity  # Rough estimate
            formatted.append(
                f"- {outcome.upper()}: {position.quantity} shares @ ${position.avg_price:.3f} (Est. P&L: ${pnl_estimate:+.2f})"
            )

        return "\n".join(formatted)

    def _get_category_context(self, category: str) -> str:
        """Get category-specific context for analysis"""
        category_contexts = {
            "politics": "Consider polling data, historical election patterns, and current political climate",
            "crypto": "Analyze technical indicators, market sentiment, and regulatory developments",
            "sports": "Consider team performance, player injuries, and historical matchup data",
            "tech": "Evaluate technological feasibility, company resources, and market conditions",
            "entertainment": "Consider industry trends, box office patterns, and audience sentiment",
            "economics": "Analyze economic indicators, policy impacts, and market fundamentals",
        }

        # Ensure category is not None before calling lower()
        if category is None:
            return "Consider market fundamentals and available information"
            
        return category_contexts.get(
            category.lower(), "Consider market fundamentals and available information"
        )

    def _get_prediction_prompt(self) -> str:
        """Get the system prompt for prediction market decisions"""
        return """You are a professional prediction market trader with expertise in analyzing various market categories. Make data-driven trading decisions based on comprehensive market analysis.

Trading Rules:
- Only recommend BUY if you believe the current odds undervalue the true probability
- Only recommend SELL if you have existing positions and want to realize profits or cut losses
- Use HOLD when the market seems efficiently priced or you lack conviction
- Consider market liquidity, time to resolution, and your portfolio concentration
- Factor in transaction costs (commission) when evaluating small trades
- Manage risk by avoiding over-concentration in any single market

Position Sizing Guidelines:
- Small conviction: 1-5 shares
- Medium conviction: 6-15 shares
- High conviction: 16-25 shares (only with strong fundamentals)
- Account size considerations: Don't risk more than 10% of portfolio on one market

For prediction markets, specify:
- action: "buy", "sell", or "hold"
- outcome: "yes" or "no" (which outcome you're trading)
- quantity: Number of shares (1-25 based on conviction)
- confidence: Your confidence level (0.0-1.0) in your prediction
- reasoning: Detailed explanation including market assessment and risk factors

Respond with JSON format:
{
    "action": "buy/sell/hold",
    "outcome": "yes/no",
    "quantity": 10,
    "confidence": 0.7,
    "reasoning": "Comprehensive explanation including fundamental analysis, risk assessment, and position sizing rationale"
}"""


class PolymarketTradingSystem:
    """Trading system for prediction markets using real market data"""

    def __init__(self):
        self.agents: List[AIPolymarketAgent] = []
        self.accounts: Dict[str, PolymarketAccount] = {}
        self.iteration = 0
        self.start_time = datetime.now()

    def _fetch_markets(self) -> List[Dict]:
        """Fetch prediction markets"""
        try:
            from ..fetchers.polymarket_fetcher import PolymarketFetcher
            fetcher = PolymarketFetcher()
            
            # Get active markets using the correct method name
            markets = fetcher.fetch_markets(limit=10)
            if markets and len(markets) > 0:
                # Add outcome data to each market and validate
                enhanced_markets = []
                for market in markets:
                    # Ensure market has a valid ID
                    if not market.get("id"):
                        continue  # Skip markets without valid IDs
                    
                    # Add mock outcomes if not present
                    if "outcomes" not in market or not market["outcomes"]:
                        import random
                        yes_price = random.uniform(0.2, 0.8)
                        no_price = 1.0 - yes_price
                        
                        market["outcomes"] = [
                            {"outcome": "yes", "price": yes_price},
                            {"outcome": "no", "price": no_price}
                        ]
                    
                    # Ensure market has required fields with defaults
                    market.setdefault("status", "active")
                    market.setdefault("title", f"Market {market['id']}")
                    market.setdefault("category", "unknown")
                    market.setdefault("total_volume", 0)
                    market.setdefault("total_liquidity", 0)
                    
                    if market.get("status") == "active":
                        enhanced_markets.append(market)
                
                if enhanced_markets:
                    return enhanced_markets[:10]  # Return max 10 markets
            
        except Exception as e:
            print(f"⚠️ Failed to fetch markets: {e}")
        
        # Fallback to mock markets - ensure they always have valid IDs
        return self._get_mock_markets()

    def _get_mock_markets(self) -> List[Dict]:
        """Get mock prediction markets for testing"""
        import random

        mock_markets = [
            {
                "id": "bitcoin_100k_2024",
                "title": "Will Bitcoin reach $100,000 by end of 2024?",
                "category": "crypto",
                "description": "Bitcoin price prediction for end of 2024",
                "end_date": "2024-12-31T23:59:59Z",
                "status": "active",
                "total_volume": random.uniform(80000, 800000),
                "total_liquidity": random.uniform(30000, 150000),
                "outcomes": [
                    {"outcome": "yes", "price": random.uniform(0.25, 0.45)},
                    {"outcome": "no", "price": random.uniform(0.55, 0.75)},
                ],
            },
            {
                "id": "us_election_2024",
                "title": "Will Democrats win the 2024 US Presidential Election?",
                "category": "politics",
                "description": "2024 US Presidential Election outcome prediction",
                "end_date": "2024-11-05T23:59:59Z",
                "status": "active",
                "total_volume": random.uniform(200000, 2000000),
                "total_liquidity": random.uniform(100000, 500000),
                "outcomes": [
                    {"outcome": "yes", "price": random.uniform(0.45, 0.55)},
                    {"outcome": "no", "price": random.uniform(0.45, 0.55)},
                ],
            },
            {
                "id": "agi_breakthrough_2025",
                "title": "Will AGI be achieved by major tech company by 2025?",
                "category": "tech",
                "description": "Artificial General Intelligence breakthrough prediction",
                "end_date": "2025-12-31T23:59:59Z",
                "status": "active",
                "total_volume": random.uniform(50000, 500000),
                "total_liquidity": random.uniform(25000, 125000),
                "outcomes": [
                    {"outcome": "yes", "price": random.uniform(0.15, 0.35)},
                    {"outcome": "no", "price": random.uniform(0.65, 0.85)},
                ],
            },
            {
                "id": "climate_target_2024",
                "title": "Will global CO2 emissions decrease by 5% in 2024?",
                "category": "economics",
                "description": "Climate change and emissions reduction target",
                "end_date": "2024-12-31T23:59:59Z",
                "status": "active",
                "total_volume": random.uniform(30000, 300000),
                "total_liquidity": random.uniform(15000, 75000),
                "outcomes": [
                    {"outcome": "yes", "price": random.uniform(0.2, 0.4)},
                    {"outcome": "no", "price": random.uniform(0.6, 0.8)},
                ],
            },
        ]

        # Normalize prices so they sum to ~1
        for market in mock_markets:
            outcomes = market["outcomes"]
            if len(outcomes) == 2:
                total_price = sum(o["price"] for o in outcomes)
                if total_price > 0:
                    for outcome in outcomes:
                        outcome["price"] = outcome["price"] / total_price

        return mock_markets

    def add_agent(
        self, name: str, initial_cash: float = 500.0, model_name: str = "gpt-4o-mini"
    ):
        """Add an AI prediction market agent"""
        agent = AIPolymarketAgent(name, model_name)
        account = create_polymarket_account(initial_cash, 0.02)  # 2% commission

        self.agents.append(agent)
        self.accounts[name] = account

        print(f"✅ Added prediction market agent {name} with ${initial_cash:.2f}")

    def run_cycle(self, markets: List[Dict]):
        """Run one trading cycle across prediction markets"""
        self.iteration += 1
        print(f"\n🔄 Cycle #{self.iteration} - {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 80)

        if not markets:
            print("❌ No active markets available, skipping cycle")
            return

        # Display market info
        market_info = []
        for market in markets[:3]:  # Show first 3 markets
            market_id = market.get("id", "unknown")
            if market_id is None or market_id == "":
                market_id = "unknown"
                print(f"⚠️ Warning: Found market with None/empty ID: {market}")

            title = market.get("title", "Unknown")
            title_short = title[:50] + "..." if len(title) > 50 else title
            outcomes = market.get("outcomes", [])
            yes_price = next(
                (o["price"] for o in outcomes if o.get("outcome") == "yes"), 0.5
            )
            market_info.append(f"{market_id}: {yes_price:.2f}")

        print(f"🎯 Active Markets: {' | '.join(market_info)}")

        # Each agent analyzes markets and may take action
        for agent in self.agents:
            account = self.accounts[agent.name]

            print(f"\n🤖 {agent.name}:")

            actions_taken = 0
            # Agent considers each market
            for market in markets:
                market_id = market.get("id", "unknown")

                # Agent generates PolymarketAction (or None)
                prediction_action = agent.generate_action(market, account)

                if prediction_action:
                    outcome_display = prediction_action.outcome.upper()
                    print(
                        f"  {market_id}: {prediction_action.action.upper()} {prediction_action.quantity} {outcome_display} @ ${prediction_action.price:.3f}"
                    )

                    # Account processes PolymarketAction
                    success, message, transaction = account.execute_action(
                        prediction_action
                    )

                    status = "✅" if success else "❌"
                    print(f"    Result: {status} {message}")

                    if success:
                        actions_taken += 1

            if actions_taken == 0:
                print("  No actions taken across markets")

            # Show account status
            try:
                evaluation = account.evaluate()
                total_value = evaluation["portfolio_summary"]["total_value"]
                return_pct = evaluation["portfolio_summary"]["return_pct"]

                print(f"  Portfolio: ${total_value:.2f} ({return_pct:+.1f}%)")
                print(f"  Cash: ${account.cash_balance:.2f}")

                active_positions = account.get_active_positions()
                if active_positions:
                    positions = []
                    for pos_key, pos in list(active_positions.items())[
                        :3
                    ]:  # Show first 3
                        positions.append(
                            f"{pos.market_id}_{pos.outcome}({pos.quantity:.0f})"
                        )
                    pos_str = ", ".join(positions)
                    if len(active_positions) > 3:
                        pos_str += f" +{len(active_positions)-3} more"
                    print(f"  Positions: {pos_str}")

            except Exception as e:
                print(f"  ⚠️ Evaluation failed: {e}")

    def print_summary(self):
        """Print system summary"""
        print("\n📊 Prediction Market Summary")
        print("=" * 70)

        total_initial = len(self.agents) * 500.0  # Default initial cash
        total_current = 0.0

        for agent in self.agents:
            account = self.accounts[agent.name]

            try:
                evaluation = account.evaluate()
                total_value = evaluation["portfolio_summary"]["total_value"]
                return_pct = evaluation["portfolio_summary"]["return_pct"]
            except:
                total_value = account.cash_balance
                return_pct = (total_value - 500.0) / 500.0 * 100

            trades = len(account.transactions)
            total_current += total_value

            # Show positions
            active_positions = account.get_active_positions()
            pos_count = len(active_positions)
            markets_traded = len(
                set(pos.market_id for pos in active_positions.values())
            )

            print(
                f"{agent.name}: ${total_value:.2f} ({return_pct:+.1f}%) | {trades} trades | {markets_traded} markets | {pos_count} positions"
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

    def run(self, cycles: int = 5, interval: float = 3.0):
        """Run the prediction market trading system"""
        print("🎯 AI Prediction Market Trading System")
        print(f"🔄 Cycles: {cycles}")
        print(f"🤖 AI Agents: {len(self.agents)}")
        print("📊 Data Source: Polymarket API with fallback")

        try:
            for cycle in range(cycles):
                # Fetch fresh market data each cycle
                markets = self._fetch_markets()
                self.run_cycle(markets)
                self.print_summary()

                if cycle < cycles - 1:
                    print(f"\n⏳ Waiting {interval}s...")
                    time.sleep(interval)

        except KeyboardInterrupt:
            print("\n⏹️ Trading stopped by user")

        print("\n🏁 Prediction market trading completed!")
        self.print_summary()


# Convenience functions
def create_polymarket_agent(
    name: str, model_name: str = "gpt-4o-mini"
) -> AIPolymarketAgent:
    """Create a new AI polymarket agent"""
    return AIPolymarketAgent(name, model_name)


def create_polymarket_trading_system() -> PolymarketTradingSystem:
    """Create a new polymarket trading system"""
    return PolymarketTradingSystem()

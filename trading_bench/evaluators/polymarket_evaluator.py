import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Union, Optional


def eval_polymarket(actions: Union[str, dict, List[dict]], 
                   market_outcomes: Optional[Dict[str, Dict]] = None) -> dict:
    """
    Polymarket prediction market evaluator for calculating trading strategy returns.
    
    Args:
        actions: JSON string or dict/list of dicts containing trading actions:
                {
                    "market_id": "market_123",
                    "outcome": "yes" or "no",
                    "action": "buy" or "sell", 
                    "timestamp": "2024-01-01",
                    "price": 0.65,  # price range 0-1
                    "quantity": 100,  # number of shares purchased
                    "confidence": 0.8  # optional: confidence level
                }
        market_outcomes: Optional dict containing actual market results
                        {"market_123": {"result": "yes", "resolution_date": "2024-12-31"}}
    
    Returns:
        dict: Detailed evaluation results including returns, accuracy, and other metrics
    """
    # Parse JSON string
    if isinstance(actions, str):
        actions = json.loads(actions)
    
    # Convert single action to list
    if isinstance(actions, dict):
        actions = [actions]
    
    # Initialize tracking variables
    positions = {}  # Track positions: market_id -> {outcome -> {quantity, avg_price, timestamps}}
    realized_pnl = 0.0
    unrealized_pnl = 0.0
    total_trades = 0
    successful_predictions = 0
    total_volume = 0.0
    
    # Generate mock outcomes for evaluation if none provided
    if market_outcomes is None:
        market_outcomes = _generate_mock_outcomes(actions)
    
    print("🎯 Polymarket Trading Evaluation Started")
    print("=" * 50)
    
    # Process each trading action
    for action in actions:
        market_id = action['market_id']
        outcome = action['outcome'].lower()  # 'yes' or 'no'
        action_type = action['action'].lower()  # 'buy' or 'sell'
        timestamp = action['timestamp']
        price = action['price']  # should be between 0-1
        quantity = action.get('quantity', 1)
        confidence = action.get('confidence', 0.5)
        
        # Validate price range
        if not (0 <= price <= 1):
            print(f"⚠️  Warning: Price {price} outside valid range [0, 1]")
            continue
        
        # Initialize market position
        if market_id not in positions:
            positions[market_id] = {'yes': {'quantity': 0, 'avg_price': 0.0, 'timestamps': []},
                                  'no': {'quantity': 0, 'avg_price': 0.0, 'timestamps': []}}
        
        position = positions[market_id][outcome]
        
        # Execute trade
        if action_type == 'buy':
            # Buy shares
            current_qty = position['quantity']
            current_avg = position['avg_price']
            new_qty = current_qty + quantity
            
            # Update average price
            if new_qty > 0:
                position['avg_price'] = (current_qty * current_avg + quantity * price) / new_qty
            position['quantity'] = new_qty
            position['timestamps'].append(timestamp)
            
            total_volume += quantity * price
            
        elif action_type == 'sell':
            # Sell shares
            if position['quantity'] >= quantity:
                # Calculate realized profit
                avg_price = position['avg_price']
                profit = (price - avg_price) * quantity
                realized_pnl += profit
                
                # Update position
                position['quantity'] -= quantity
                position['timestamps'].append(timestamp)
                
                total_volume += quantity * price
                
                print(f"💰 Sold {quantity} {outcome.upper()} @ ${price:.3f} "
                      f"(bought @ ${avg_price:.3f}) = ${profit:.2f}")
            else:
                print(f"⚠️  Warning: Insufficient {market_id} {outcome} shares to sell {quantity}")
        
        total_trades += 1
    
    # Calculate unrealized returns and prediction accuracy
    for market_id, market_position in positions.items():
        market_result = market_outcomes.get(market_id, {})
        winning_outcome = market_result.get('result', 'unknown')
        
        for outcome, position in market_position.items():
            if position['quantity'] > 0:
                avg_price = position['avg_price']
                quantity = position['quantity']
                
                # Calculate unrealized returns
                if winning_outcome == outcome:
                    # Correct prediction, share value is 1
                    final_value = 1.0
                    prediction_correct = True
                elif winning_outcome in ['yes', 'no']:
                    # Incorrect prediction, share value is 0
                    final_value = 0.0
                    prediction_correct = False
                else:
                    # Market unresolved, use simulated current price
                    final_value = _simulate_current_price(outcome, avg_price)
                    prediction_correct = None
                
                unrealized_profit = (final_value - avg_price) * quantity
                unrealized_pnl += unrealized_profit
                
                # Track prediction accuracy
                if prediction_correct is not None:
                    if prediction_correct:
                        successful_predictions += 1
                
                print(f"📊 {market_id} {outcome.upper()}: "
                      f"Holding {quantity} shares @ ${avg_price:.3f}")
                print(f"   Current value: ${final_value:.3f} | "
                      f"Unrealized P&L: ${unrealized_profit:.2f}")
                if winning_outcome != 'unknown':
                    result_emoji = "✅" if prediction_correct else "❌"
                    print(f"   Market result: {winning_outcome.upper()} {result_emoji}")
    
    # Calculate comprehensive metrics
    total_pnl = realized_pnl + unrealized_pnl
    accuracy = successful_predictions / len(market_outcomes) if market_outcomes else 0
    avg_trade_size = total_volume / total_trades if total_trades > 0 else 0
    
    # Calculate risk-adjusted returns (simplified Sharpe ratio)
    risk_free_rate = 0.02  # Assume 2% risk-free rate
    volatility = abs(total_pnl) * 0.2  # Simplified volatility estimate
    sharpe_ratio = (total_pnl - risk_free_rate) / volatility if volatility > 0 else 0
    
    # Evaluation results
    evaluation_result = {
        'total_pnl': total_pnl,
        'realized_pnl': realized_pnl,
        'unrealized_pnl': unrealized_pnl,
        'total_trades': total_trades,
        'total_volume': total_volume,
        'average_trade_size': avg_trade_size,
        'prediction_accuracy': accuracy,
        'successful_predictions': successful_predictions,
        'total_markets': len(market_outcomes),
        'sharpe_ratio': sharpe_ratio,
        'positions': positions,
        'market_outcomes': market_outcomes
    }
    
    # Print summary
    print("\n📈 Evaluation Summary")
    print("=" * 30)
    print(f"Total P&L: ${total_pnl:.2f}")
    print(f"Realized P&L: ${realized_pnl:.2f}")
    print(f"Unrealized P&L: ${unrealized_pnl:.2f}")
    print(f"Total trades: {total_trades}")
    print(f"Prediction accuracy: {accuracy:.1%}")
    print(f"Sharpe ratio: {sharpe_ratio:.2f}")
    
    return evaluation_result


def _generate_mock_outcomes(actions: List[dict]) -> Dict[str, Dict]:
    """Generate mock market outcomes for evaluation"""
    market_outcomes = {}
    market_ids = set(action['market_id'] for action in actions)
    
    for market_id in market_ids:
        # Randomly generate market results
        result = random.choice(['yes', 'no'])
        resolution_date = (datetime.now() + timedelta(days=random.randint(1, 365))).strftime('%Y-%m-%d')
        
        market_outcomes[market_id] = {
            'result': result,
            'resolution_date': resolution_date,
            'confidence': random.uniform(0.8, 0.95)
        }
    
    return market_outcomes


def _simulate_current_price(outcome: str, avg_price: float) -> float:
    """Simulate current market price"""
    # Generate reasonable current price based on average price
    volatility = 0.1  # 10% volatility
    price_change = random.uniform(-volatility, volatility)
    current_price = avg_price * (1 + price_change)
    
    # Ensure price is within 0-1 range
    return max(0.0, min(1.0, current_price))


def calculate_kelly_criterion(win_rate: float, avg_win: float, avg_loss: float) -> float:
    """
    Calculate Kelly criterion for optimal bet sizing
    
    Args:
        win_rate: Win rate (0-1)
        avg_win: Average profit on winning trades
        avg_loss: Average loss on losing trades
    
    Returns:
        float: Recommended bet fraction
    """
    if avg_loss <= 0:
        return 0.0
    
    b = avg_win / avg_loss  # Odds ratio
    p = win_rate  # Win probability
    q = 1 - p  # Loss probability
    
    kelly_fraction = (b * p - q) / b
    
    # Use conservative 1/4 Kelly for safety
    return max(0, min(0.25, kelly_fraction * 0.25))


def analyze_market_efficiency(actions: List[dict], market_outcomes: Dict[str, Dict]) -> dict:
    """
    Analyze market efficiency and arbitrage opportunities
    
    Args:
        actions: List of trading actions
        market_outcomes: Market results
    
    Returns:
        dict: Market efficiency analysis results
    """
    market_analysis = {}
    
    for action in actions:
        market_id = action['market_id']
        if market_id not in market_analysis:
            market_analysis[market_id] = {'prices': [], 'outcomes': []}
        
        market_analysis[market_id]['prices'].append(action['price'])
        market_analysis[market_id]['outcomes'].append(action['outcome'])
    
    efficiency_results = {}
    
    for market_id, data in market_analysis.items():
        prices = data['prices']
        if len(prices) < 2:
            continue
        
        # Calculate price volatility
        price_volatility = (max(prices) - min(prices)) / max(prices) if max(prices) > 0 else 0
        
        # Check for arbitrage opportunities (YES + NO prices should sum close to 1)
        arbitrage_opportunities = []
        # More complex arbitrage detection logic can be added here
        
        efficiency_results[market_id] = {
            'price_volatility': price_volatility,
            'arbitrage_opportunities': arbitrage_opportunities,
            'market_depth': len(prices),
            'efficiency_score': 1 - price_volatility  # Simplified efficiency score
        }
    
    return efficiency_results


class PolymarketEvaluator:
    """
    Polymarket prediction market evaluator class
    """
    
    def __init__(self, risk_free_rate: float = 0.02):
        self.risk_free_rate = risk_free_rate
        self.evaluation_history = []
    
    def evaluate(self, actions: Union[str, dict, List[dict]], 
                market_outcomes: Optional[Dict[str, Dict]] = None) -> dict:
        """Evaluate trading strategy"""
        result = eval_polymarket(actions, market_outcomes)
        self.evaluation_history.append({
            'timestamp': datetime.now().isoformat(),
            'result': result
        })
        return result
    
    def get_performance_metrics(self) -> dict:
        """Get historical performance metrics"""
        if not self.evaluation_history:
            return {}
        
        total_pnls = [eval_result['result']['total_pnl'] for eval_result in self.evaluation_history]
        accuracies = [eval_result['result']['prediction_accuracy'] for eval_result in self.evaluation_history]
        
        return {
            'average_pnl': sum(total_pnls) / len(total_pnls),
            'total_evaluations': len(self.evaluation_history),
            'average_accuracy': sum(accuracies) / len(accuracies),
            'best_performance': max(total_pnls),
            'worst_performance': min(total_pnls),
            'consistency_score': 1 - (max(total_pnls) - min(total_pnls)) / max(abs(max(total_pnls)), abs(min(total_pnls)), 1)
        } 
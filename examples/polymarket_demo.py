#!/usr/bin/env python3
"""
Polymarket prediction market evaluator demonstration script
Shows how to use the Polymarket evaluator to assess prediction market trading strategies
"""

import os
import sys

# Add trading_bench to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading_bench.evaluators.polymarket_evaluator import (
    PolymarketEvaluator,
    analyze_market_efficiency,
    calculate_kelly_criterion,
    eval_polymarket,
)


def demonstrate_basic_evaluation():
    """Demonstrate basic Polymarket evaluation functionality"""
    print('🎯 Demo 1: Basic Polymarket Prediction Market Evaluation')
    print('=' * 60)

    # Simulate some trading actions
    actions = [
        {
            'market_id': 'election_2024',
            'outcome': 'yes',
            'action': 'buy',
            'timestamp': '2024-01-15',
            'price': 0.65,
            'quantity': 100,
            'confidence': 0.8,
        },
        {
            'market_id': 'election_2024',
            'outcome': 'yes',
            'action': 'sell',
            'timestamp': '2024-02-01',
            'price': 0.72,
            'quantity': 50,
            'confidence': 0.7,
        },
        {
            'market_id': 'bitcoin_100k',
            'outcome': 'no',
            'action': 'buy',
            'timestamp': '2024-01-20',
            'price': 0.45,
            'quantity': 200,
            'confidence': 0.6,
        },
        {
            'market_id': 'bitcoin_100k',
            'outcome': 'yes',
            'action': 'buy',
            'timestamp': '2024-03-01',
            'price': 0.55,
            'quantity': 150,
            'confidence': 0.9,
        },
    ]

    # Define market outcomes
    market_outcomes = {
        'election_2024': {
            'result': 'yes',
            'resolution_date': '2024-11-06',
            'confidence': 0.95,
        },
        'bitcoin_100k': {
            'result': 'yes',
            'resolution_date': '2024-12-31',
            'confidence': 0.9,
        },
    }

    # Execute evaluation
    result = eval_polymarket(actions, market_outcomes)

    print('\n✨ Detailed evaluation results:')
    print(f"  Prediction accuracy: {result['prediction_accuracy']:.1%}")
    print(
        f"  Successful predictions: {result['successful_predictions']}/{result['total_markets']}"
    )
    print(f"  Average trade size: ${result['average_trade_size']:.2f}")
    print(f"  Total volume: ${result['total_volume']:.2f}")


def demonstrate_evaluator_class():
    """Demonstrate PolymarketEvaluator class usage"""
    print('\n🔍 Demo 2: PolymarketEvaluator Class Usage')
    print('=' * 60)

    # Create evaluator instance
    evaluator = PolymarketEvaluator(risk_free_rate=0.03)

    # Multiple evaluations of different strategies
    strategies = [
        # Strategy 1: Conservative - only buy high probability events
        [
            {
                'market_id': 'strategy1_market',
                'outcome': 'yes',
                'action': 'buy',
                'timestamp': '2024-01-01',
                'price': 0.8,
                'quantity': 50,
                'confidence': 0.9,
            },
            {
                'market_id': 'strategy1_market',
                'outcome': 'yes',
                'action': 'sell',
                'timestamp': '2024-01-15',
                'price': 0.85,
                'quantity': 50,
                'confidence': 0.85,
            },
        ],
        # Strategy 2: Aggressive - buy low-value events
        [
            {
                'market_id': 'strategy2_market',
                'outcome': 'yes',
                'action': 'buy',
                'timestamp': '2024-01-01',
                'price': 0.2,
                'quantity': 200,
                'confidence': 0.7,
            },
            {
                'market_id': 'strategy2_market',
                'outcome': 'yes',
                'action': 'sell',
                'timestamp': '2024-01-15',
                'price': 0.35,
                'quantity': 200,
                'confidence': 0.6,
            },
        ],
        # Strategy 3: Hedging - buy both sides
        [
            {
                'market_id': 'strategy3_market',
                'outcome': 'yes',
                'action': 'buy',
                'timestamp': '2024-01-01',
                'price': 0.6,
                'quantity': 100,
                'confidence': 0.6,
            },
            {
                'market_id': 'strategy3_market',
                'outcome': 'no',
                'action': 'buy',
                'timestamp': '2024-01-01',
                'price': 0.4,
                'quantity': 100,
                'confidence': 0.4,
            },
        ],
    ]

    # Define different market outcomes for each strategy
    strategy_outcomes = [
        {'strategy1_market': {'result': 'yes', 'resolution_date': '2024-02-01'}},
        {'strategy2_market': {'result': 'yes', 'resolution_date': '2024-02-01'}},
        {'strategy3_market': {'result': 'no', 'resolution_date': '2024-02-01'}},
    ]

    print('Evaluating multiple trading strategies:')
    for i, (strategy, outcomes) in enumerate(
        zip(strategies, strategy_outcomes, strict=False), 1
    ):
        print(f'\nStrategy {i}:')
        result = evaluator.evaluate(strategy, outcomes)
        print(f"  Returns: ${result['total_pnl']:.2f}")
        print(f"  Accuracy: {result['prediction_accuracy']:.1%}")

    # Get historical performance metrics
    performance = evaluator.get_performance_metrics()
    print('\n📊 Historical Performance Summary:')
    print(f"  Average returns: ${performance['average_pnl']:.2f}")
    print(f"  Total evaluations: {performance['total_evaluations']}")
    print(f"  Average accuracy: {performance['average_accuracy']:.1%}")
    print(f"  Best performance: ${performance['best_performance']:.2f}")
    print(f"  Worst performance: ${performance['worst_performance']:.2f}")
    print(f"  Consistency score: {performance['consistency_score']:.2f}")


def demonstrate_kelly_criterion():
    """Demonstrate Kelly criterion calculation"""
    print('\n📐 Demo 3: Kelly Criterion Optimal Bet Sizing')
    print('=' * 60)

    # Different market scenarios
    scenarios = [
        {
            'name': 'High win rate, low odds',
            'win_rate': 0.8,
            'avg_win': 20,
            'avg_loss': 80,
        },
        {
            'name': 'Low win rate, high odds',
            'win_rate': 0.3,
            'avg_win': 200,
            'avg_loss': 100,
        },
        {'name': 'Balanced scenario', 'win_rate': 0.6, 'avg_win': 100, 'avg_loss': 100},
        {
            'name': 'Unfavorable scenario',
            'win_rate': 0.4,
            'avg_win': 50,
            'avg_loss': 100,
        },
    ]

    for scenario in scenarios:
        kelly_fraction = calculate_kelly_criterion(
            scenario['win_rate'], scenario['avg_win'], scenario['avg_loss']
        )

        print(f"{scenario['name']}:")
        print(f"  Win rate: {scenario['win_rate']:.1%}")
        print(f"  Average profit: ${scenario['avg_win']}")
        print(f"  Average loss: ${scenario['avg_loss']}")
        print(f'  Recommended bet fraction: {kelly_fraction:.1%}')
        print()


def demonstrate_market_efficiency():
    """Demonstrate market efficiency analysis"""
    print('\n⚖️ Demo 4: Market Efficiency Analysis')
    print('=' * 60)

    # Simulate trading data for a market
    market_actions = [
        {
            'market_id': 'efficiency_test',
            'outcome': 'yes',
            'action': 'buy',
            'timestamp': '2024-01-01',
            'price': 0.5,
            'quantity': 100,
        },
        {
            'market_id': 'efficiency_test',
            'outcome': 'yes',
            'action': 'buy',
            'timestamp': '2024-01-02',
            'price': 0.52,
            'quantity': 150,
        },
        {
            'market_id': 'efficiency_test',
            'outcome': 'no',
            'action': 'buy',
            'timestamp': '2024-01-02',
            'price': 0.48,
            'quantity': 120,
        },
        {
            'market_id': 'efficiency_test',
            'outcome': 'yes',
            'action': 'sell',
            'timestamp': '2024-01-03',
            'price': 0.58,
            'quantity': 100,
        },
        {
            'market_id': 'efficiency_test',
            'outcome': 'yes',
            'action': 'buy',
            'timestamp': '2024-01-04',
            'price': 0.65,
            'quantity': 80,
        },
    ]

    market_outcomes = {
        'efficiency_test': {'result': 'yes', 'resolution_date': '2024-02-01'}
    }

    # Analyze market efficiency
    efficiency_analysis = analyze_market_efficiency(market_actions, market_outcomes)

    for market_id, analysis in efficiency_analysis.items():
        print(f'Market {market_id}:')
        print(f"  Price volatility: {analysis['price_volatility']:.1%}")
        print(f"  Market depth: {analysis['market_depth']} trades")
        print(f"  Efficiency score: {analysis['efficiency_score']:.2f}/1.0")
        print(f"  Arbitrage opportunities: {len(analysis['arbitrage_opportunities'])}")


def demonstrate_json_input():
    """Demonstrate JSON format input"""
    print('\n📄 Demo 5: JSON Format Input')
    print('=' * 60)

    # JSON string format trading data
    json_actions = """
    [
        {
            "market_id": "json_test_market",
            "outcome": "yes",
            "action": "buy",
            "timestamp": "2024-01-10",
            "price": 0.45,
            "quantity": 300,
            "confidence": 0.75
        },
        {
            "market_id": "json_test_market",
            "outcome": "yes",
            "action": "sell",
            "timestamp": "2024-01-25",
            "price": 0.62,
            "quantity": 150,
            "confidence": 0.8
        }
    ]
    """

    print('Input JSON data:')
    print(json_actions)

    # Use JSON string for evaluation
    result = eval_polymarket(json_actions)

    print('\nEvaluation results (using simulated market outcomes):')
    print(f"Total returns: ${result['total_pnl']:.2f}")
    print(f"Number of trades: {result['total_trades']}")


def demonstrate_real_world_scenario():
    """Demonstrate real-world trading scenario"""
    print('\n🌍 Demo 6: Real-World Trading Scenario')
    print('=' * 60)

    # Simulate a more complex real trading scenario
    real_actions = [
        # 2024 US Presidential Election
        {
            'market_id': 'us_election_2024',
            'outcome': 'yes',
            'action': 'buy',
            'timestamp': '2024-01-01',
            'price': 0.48,
            'quantity': 500,
            'confidence': 0.6,
        },
        {
            'market_id': 'us_election_2024',
            'outcome': 'yes',
            'action': 'buy',
            'timestamp': '2024-03-15',
            'price': 0.52,
            'quantity': 300,
            'confidence': 0.7,
        },
        {
            'market_id': 'us_election_2024',
            'outcome': 'yes',
            'action': 'sell',
            'timestamp': '2024-10-01',
            'price': 0.58,
            'quantity': 200,
            'confidence': 0.8,
        },
        # Bitcoin ETF Approval
        {
            'market_id': 'btc_etf_2024',
            'outcome': 'yes',
            'action': 'buy',
            'timestamp': '2024-01-01',
            'price': 0.75,
            'quantity': 200,
            'confidence': 0.85,
        },
        {
            'market_id': 'btc_etf_2024',
            'outcome': 'yes',
            'action': 'sell',
            'timestamp': '2024-01-10',
            'price': 0.92,
            'quantity': 200,
            'confidence': 0.95,
        },
        # Super Bowl Outcome
        {
            'market_id': 'superbowl_2024',
            'outcome': 'no',
            'action': 'buy',
            'timestamp': '2024-01-15',
            'price': 0.35,
            'quantity': 400,
            'confidence': 0.55,
        },
        # AI Technology Breakthrough
        {
            'market_id': 'agi_by_2025',
            'outcome': 'no',
            'action': 'buy',
            'timestamp': '2024-02-01',
            'price': 0.25,
            'quantity': 800,
            'confidence': 0.8,
        },
    ]

    # Real market outcomes (hypothetical)
    real_outcomes = {
        'us_election_2024': {'result': 'yes', 'resolution_date': '2024-11-06'},
        'btc_etf_2024': {'result': 'yes', 'resolution_date': '2024-01-11'},
        'superbowl_2024': {'result': 'no', 'resolution_date': '2024-02-11'},
        'agi_by_2025': {'result': 'no', 'resolution_date': '2024-12-31'},
    }

    # Execute comprehensive evaluation
    result = eval_polymarket(real_actions, real_outcomes)

    print('\n🏆 Overall Trading Performance:')
    print(f"Portfolio total returns: ${result['total_pnl']:.2f}")
    print(
        f"Return on investment: {(result['total_pnl']/result['total_volume']*100):.1f}%"
        if result['total_volume'] > 0
        else '0%'
    )
    print(f"Prediction accuracy: {result['prediction_accuracy']:.1%}")
    print(f"Sharpe ratio: {result['sharpe_ratio']:.2f}")
    print(
        f"Successful predictions: {result['successful_predictions']}/{result['total_markets']} markets"
    )

    # Analyze performance by individual markets
    print('\n📈 Detailed Performance by Market:')
    for market_id, outcome in real_outcomes.items():
        market_positions = result['positions'].get(market_id, {})
        total_market_pnl = 0

        for outcome_type, position in market_positions.items():
            if position['quantity'] > 0:
                if outcome['result'] == outcome_type:
                    pnl = (1.0 - position['avg_price']) * position['quantity']
                else:
                    pnl = (0.0 - position['avg_price']) * position['quantity']
                total_market_pnl += pnl

        result_emoji = (
            '✅' if total_market_pnl > 0 else '❌' if total_market_pnl < 0 else '➖'
        )
        print(f'  {market_id}: ${total_market_pnl:.2f} {result_emoji}')


def main():
    """Main function"""
    print('🎯 Polymarket Prediction Market Evaluator Complete Demo')
    print('=' * 80)

    try:
        # Execute all demonstrations
        demonstrate_basic_evaluation()
        demonstrate_evaluator_class()
        demonstrate_kelly_criterion()
        demonstrate_market_efficiency()
        demonstrate_json_input()
        demonstrate_real_world_scenario()

        print('\n✨ All demonstrations completed!')
        print('\n📚 Usage Guide:')
        print('1. Basic evaluation function: eval_polymarket(actions, market_outcomes)')
        print('2. Evaluator class: PolymarketEvaluator() supports historical tracking')
        print(
            '3. Kelly criterion: calculate_kelly_criterion() calculates optimal bet sizing'
        )
        print(
            '4. Market efficiency: analyze_market_efficiency() analyzes arbitrage opportunities'
        )
        print('5. Supports JSON strings, dictionaries, lists, and other input formats')
        print('6. Automatically generates simulated market outcomes for testing')

    except KeyboardInterrupt:
        print('\n\n⏹️  Demo interrupted by user')
    except Exception as e:
        print(f'\n❌ Demo error: {e}')


if __name__ == '__main__':
    main()

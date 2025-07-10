import json
from datetime import datetime, timedelta

from trading_bench.data_fetchers.stock_fetcher import fetch_price_data


def eval(actions: str | dict | list[dict]) -> float:
    """
    Simple evaluator that takes JSON format actions and returns total benefits.
    Automatically fetches latest price data to calculate benefits.

    Args:
        actions: JSON string or dict/list of actions with format:
                {
                    "ticker": "AAPL",
                    "action": "buy" or "sell",
                    "timestamp": "2025-01-01",
                    "price": 150.0,  # optional, will fetch if not provided
                    "quantity": 1    # optional, defaults to 1
                }

    Returns:
        float: Total benefits/returns compared to latest price
    """
    # Parse JSON if string
    if isinstance(actions, str):
        actions = json.loads(actions)

    # Convert single action to list
    if isinstance(actions, dict):
        actions = [actions]

    total_benefits = 0.0
    positions = {}  # Track positions: ticker -> {quantity, avg_price, timestamps}

    # Get latest date to fetch current prices
    latest_date = datetime.now().strftime('%Y-%m-%d')

    for action in actions:
        ticker = action['ticker']
        action_type = action['action'].lower()
        timestamp = action['timestamp']
        quantity = action.get('quantity', 1)

        # Get price for the action
        if 'price' in action:
            price = action['price']
        else:
            # Fetch price data for the action date
            price_data = fetch_price_data(
                ticker=ticker, start_date=timestamp, end_date=timestamp, resolution='D'
            )
            if price_data and timestamp in price_data:
                price = price_data[timestamp]['close']
            else:
                print(f'Warning: Could not fetch price for {ticker} on {timestamp}')
                continue

        # Initialize position if not exists
        if ticker not in positions:
            positions[ticker] = {'quantity': 0, 'avg_price': 0.0, 'timestamps': []}

        # Execute action
        if action_type == 'buy':
            # Update average price
            current_qty = positions[ticker]['quantity']
            current_avg = positions[ticker]['avg_price']
            new_qty = current_qty + quantity

            if new_qty > 0:
                positions[ticker]['avg_price'] = (
                    current_qty * current_avg + quantity * price
                ) / new_qty
            positions[ticker]['quantity'] = new_qty
            positions[ticker]['timestamps'].append(timestamp)

        elif action_type == 'sell':
            if positions[ticker]['quantity'] >= quantity:
                # Calculate profit/loss using action price
                avg_price = positions[ticker]['avg_price']
                profit = (price - avg_price) * quantity
                total_benefits += profit

                # Update position
                positions[ticker]['quantity'] -= quantity
                positions[ticker]['timestamps'].append(timestamp)
            else:
                print(f'Warning: Not enough shares to sell {quantity} of {ticker}')

    # Calculate unrealized gains/losses for remaining positions
    for ticker, position in positions.items():
        if position['quantity'] > 0:
            # Get latest price
            try:
                latest_price_data = fetch_price_data(
                    ticker=ticker,
                    start_date=latest_date,
                    end_date=latest_date,
                    resolution='D',
                )

                if latest_price_data and latest_date in latest_price_data:
                    latest_price = latest_price_data[latest_date]['close']
                else:
                    # Try to get most recent available price
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=7)  # Look back 7 days

                    recent_data = fetch_price_data(
                        ticker=ticker,
                        start_date=start_date.strftime('%Y-%m-%d'),
                        end_date=end_date.strftime('%Y-%m-%d'),
                        resolution='D',
                    )

                    if recent_data:
                        # Get the most recent price
                        recent_dates = sorted(recent_data.keys(), reverse=True)
                        latest_price = recent_data[recent_dates[0]]['close']
                    else:
                        print(f'Warning: Could not fetch latest price for {ticker}')
                        continue

                # Calculate unrealized profit/loss
                avg_price = position['avg_price']
                unrealized_profit = (latest_price - avg_price) * position['quantity']
                total_benefits += unrealized_profit

                print(
                    f"📊 {ticker}: Holding {position['quantity']} shares at avg ${avg_price:.2f}, current ${latest_price:.2f}"
                )
                print(f'   Unrealized P&L: ${unrealized_profit:.2f}')

            except Exception as e:
                print(f'Warning: Error fetching latest price for {ticker}: {e}')

    return total_benefits


class ReturnEvaluator:
    """
    Legacy evaluator for backward compatibility.
    """

    def evaluate(self, actions: str | dict | list[dict]) -> float:
        """Wrapper for the new eval function"""
        return eval(actions)

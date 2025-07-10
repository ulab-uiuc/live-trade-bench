from trading_bench.data_fetchers.stock_fetcher import fetch_price_data
from trading_bench.evaluator import eval
from trading_bench.model_wrapper import AIStockAnalysisModel


def run_one_trade(ticker: str, date: str, quantity: int):
    # 1. Get historical closes up to 'date'
    hist = fetch_price_data(
        ticker=ticker, start_date='2024-12-01', end_date=date, resolution='D'
    )
    closes = [hist[d]['close'] for d in sorted(hist)]

    # 2. Get actions from AI model
    model = AIStockAnalysisModel()  # assumes OPENAI_API_KEY is set
    actions = model.act(
        ticker=ticker, price_history=closes, date=date, quantity=quantity
    )

    if not actions:
        print(f'No actions recommended for {ticker} on {date}.')
        return

    # 3. Evaluate the actions
    profit = eval(actions)

    # 4. Display results
    for action in actions:
        print(
            f"Action: {action['action'].upper()} {action['quantity']}×{ticker} on {date}"
        )
        if 'confidence' in action:
            print(f"  Confidence: {action['confidence']:.2f}")
        if 'reasoning' in action:
            print(f"  Reasoning: {action['reasoning']}")

    print(f'Total Profit: ${profit:.2f}')

    return {'actions': actions, 'profit': profit}


if __name__ == '__main__':
    result = run_one_trade('AAPL', '2025-01-01', 10)
    print(f'\nFinal result: {result}')

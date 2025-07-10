from datetime import datetime, timedelta

from trading_bench.data_fetchers.news_fetcher import fetch_news_data
from trading_bench.data_fetchers.stock_fetcher import fetch_price_data
from trading_bench.evaluator import eval
from trading_bench.model_wrapper import AIStockAnalysisModel


def fetch_news_for_ticker(
    ticker: str, date: str, days_back: int = 7, max_articles: int = 5
) -> list[dict]:
    """Fetch up to `max_articles` recent news for a ticker."""
    date_obj = datetime.strptime(date, '%Y-%m-%d')
    start = (date_obj - timedelta(days=days_back)).strftime('%Y-%m-%d')
    query = f'{ticker} stock news'
    articles = fetch_news_data(query, start, date, max_pages=2)
    return articles[:max_articles] if articles else []


def run_trade(ticker: str, date: str, quantity: int, include_news: bool = True) -> dict:
    """Fetch data, run AI model, evaluate, and return results."""
    # Price data
    prices = fetch_price_data(
        ticker=ticker, start_date='2024-12-01', end_date=date, resolution='D'
    )
    closes = [prices[d]['close'] for d in sorted(prices)]
    print(f'{ticker} @ {date} — Latest close: ${closes[-1]:.2f}')

    # News data (optional)
    news = fetch_news_for_ticker(ticker, date) if include_news else []
    if include_news:
        print(f'Fetched {len(news)} news articles.')
        for idx, art in enumerate(news[:3], 1):
            print(f"  {idx}. {art['title']}")

    # AI analysis
    model = AIStockAnalysisModel()
    actions = (
        model.act(
            ticker=ticker,
            price_history=closes,
            date=date,
            quantity=quantity,
            news_data=news or None,
        )
        or []
    )

    print(actions)

    # Evaluation
    profit = eval(actions) if actions else 0.0
    print(f'Profit: ${profit:.2f}\n')

    return {
        'actions': actions,
        'profit': profit,
        'news_count': len(news),
    }


if __name__ == '__main__':
    # Single example
    run_trade('AAPL', '2025-01-01', 10)
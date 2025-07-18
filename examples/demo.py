from datetime import datetime, timedelta
from typing import Any, Dict, List

from trading_bench.evaluators import eval_stock
from trading_bench.fetchers.news_fetcher import fetch_news_data
from trading_bench.fetchers.stock_fetcher import fetch_stock_data
from trading_bench.model import AIStockAnalysisModel, PortfolioModel


def fetch_news_for_ticker(
    ticker: str, date: str, days_back: int = 7, max_articles: int = 5
) -> List[Dict[str, Any]]:
    """
    Fetch recent news articles for a given stock ticker within a date range.

    Args:
        ticker (str): Stock ticker symbol (e.g., 'AAPL').
        date (str): End date for news search in 'YYYY-MM-DD' format.
        days_back (int, optional): Number of days to look back from the end date. Defaults to 7.
        max_articles (int, optional): Maximum number of articles to return. Defaults to 5.

    Returns:
        List[Dict[str, Any]]: List of news article dictionaries, each containing title, link, snippet, date, and source.
    """
    date_obj = datetime.strptime(date, "%Y-%m-%d")
    start = (date_obj - timedelta(days=days_back)).strftime("%Y-%m-%d")
    query = f"{ticker} stock news"
    articles = fetch_news_data(query, start, date, max_pages=2)
    return articles[:max_articles] if articles else []


def run_trade(ticker: str, date: str, quantity: int, include_news: bool = True) -> dict:
    """
    Run a full trading pipeline for a given stock ticker and date.

    This function fetches price and (optionally) news data, runs the AI model to generate trading actions, evaluates the actions, and prints a summary.

    Args:
        ticker (str): Stock ticker symbol (e.g., 'AAPL').
        date (str): Date for the trade in 'YYYY-MM-DD' format.
        quantity (int): Number of shares to trade (passed to the AI model).
        include_news (bool, optional): Whether to include news data in the analysis. Defaults to True.

    Returns:
        dict: Dictionary containing actions (list), profit (float), and news_count (int).
    """
    # Single stock trading pipeline
    prices = fetch_stock_data(
        ticker=ticker, start_date="2024-12-01", end_date=date, resolution="D"
    )
    closes = [prices[d]["close"] for d in sorted(prices)]
    print(
        f"[1/4] Price Data Loaded: {ticker} up to {date}. Latest closing price: ${closes[-1]:.2f}"
    )
    news = fetch_news_for_ticker(ticker, date) if include_news else []
    if include_news:
        print(
            f"[2/4] News Data Loaded: {len(news)} recent articles found for {ticker}."
        )
        for idx, art in enumerate(news[:3], 1):
            print(
                f"    News {idx}: '{art['title']}' (Source: {art.get('source', 'Unknown')}, Date: {art.get('date', 'Unknown')})"
            )
        if len(news) > 3:
            print(f"    ...and {len(news) - 3} more articles.")
    else:
        print("[2/4] News Data Skipped: News integration is disabled.")
    print("[3/4] Running AI Stock Analysis Model to generate trading actions...")
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
    if actions:
        print(f"      AI Model Output: {len(actions)} action(s) generated.")
        for i, act in enumerate(actions, 1):
            print(
                f"      Action {i}: {act['action'].upper()} {act['quantity']} shares at ${act.get('price', 0):.2f} (Confidence: {act.get('confidence', 0):.2f})"
            )
            print(f"      Reasoning: {act.get('reasoning', '')}")
            if "news_sentiment" in act:
                print(
                    f"      News Sentiment: {act['news_sentiment']} (Impact: {act.get('news_impact', 'n/a')})"
                )
    else:
        print("      AI Model Output: No actionable trade signals generated.")
    print("[4/4] Evaluating trading actions for profit/loss...")
    profit = eval_stock(actions) if actions else 0.0
    print(f"    Evaluation Result: Total profit/loss = ${profit:.2f}\n")
    return {
        "actions": actions,
        "profit": profit,
        "news_count": len(news),
    }


def run_portfolio_demo(tickers: List[str], date: str, days_back: int = 7, max_articles: int = 5, total_capital: float = None):
    """
    Demo for PortfolioModel: fetch price/news for a stock pool, call PortfolioModel.act, and print the LLM's joint decision.
    """
    print("\n=== PortfolioModel: Joint LLM Decision for Stock Pool ===")
    # Fetch price histories and news for all tickers
    price_histories = {}
    news_data = {}
    for ticker in tickers:
        prices = fetch_stock_data(
            ticker=ticker, start_date=(datetime.strptime(date, "%Y-%m-%d") - timedelta(days=days_back+10)).strftime("%Y-%m-%d"), end_date=date, resolution="D"
        )
        closes = [prices[d]["close"] for d in sorted(prices)] if prices else []
        price_histories[ticker] = closes
        news_data[ticker] = fetch_news_for_ticker(ticker, date, days_back, max_articles)
    # Call PortfolioModel
    model = PortfolioModel()
    actions = model.act(
        tickers=tickers,
        price_histories=price_histories,
        news_data=news_data,
        date=date,
        total_capital=total_capital,
    )
    print("\nLLM Portfolio Decision:")
    for act in actions:
        print(f"  {act['ticker']}: {act['action'].upper()} | Weight: {act['weight']:.2f} | Confidence: {act['confidence']:.2f}")
        print(f"    Reasoning: {act['reasoning']}")
    return actions


if __name__ == "__main__":
    # print("=== Live Trading Bench: Single Stock Example ===")
    # result = run_trade("AAPL", "2025-01-01", 10)
    # print("Live Backtest completed. Summary:")
    # print(f"  Actions taken: {len(result['actions'])}")
    # print(f"  Total profit/loss: ${result['profit']:.2f}")
    # print(f"  News articles used: {result['news_count']}")

    print("\n=== Live Trading Bench: Stock Pool Example (LLM Joint Decision) ===")
    nasdaq_sample = ["AAPL", "MSFT", "GOOGL"]
    run_portfolio_demo(nasdaq_sample, "2025-01-01", days_back=7, max_articles=3, total_capital=100000)

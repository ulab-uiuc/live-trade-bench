import random

from app.schemas import (
    ModelStatus,
    NewsCategory,
    NewsImpact,
    NewsItem,
    Trade,
    TradeType,
    TradingModel,
)

# Sample trading models data
SAMPLE_MODELS: list[TradingModel] = [
    TradingModel(
        id='1',
        name='LSTM Deep Learning Model',
        performance=78.5,
        accuracy=82.3,
        trades=145,
        profit=2340.50,
        status=ModelStatus.ACTIVE,
    ),
    TradingModel(
        id='2',
        name='Random Forest Classifier',
        performance=65.2,
        accuracy=71.8,
        trades=89,
        profit=1250.75,
        status=ModelStatus.ACTIVE,
    ),
    TradingModel(
        id='3',
        name='XGBoost Regressor',
        performance=71.9,
        accuracy=76.4,
        trades=112,
        profit=1890.25,
        status=ModelStatus.INACTIVE,
    ),
    TradingModel(
        id='4',
        name='Support Vector Machine',
        performance=55.8,
        accuracy=62.1,
        trades=67,
        profit=-450.30,
        status=ModelStatus.TRAINING,
    ),
    TradingModel(
        id='5',
        name='Neural Network Ensemble',
        performance=83.2,
        accuracy=87.6,
        trades=203,
        profit=4120.80,
        status=ModelStatus.ACTIVE,
    ),
]


def get_models_data() -> list[TradingModel]:
    """Get all trading models with some random variation in performance."""
    models = []
    for model in SAMPLE_MODELS:
        # Add some random variation to make it more realistic
        variation = random.uniform(-2, 2)
        updated_model = model.model_copy()
        updated_model.performance = max(0, min(100, model.performance + variation))
        models.append(updated_model)
    return models


def get_trades_data() -> list[Trade]:
    """Get trading history data."""
    # Return empty list since SAMPLE_TRADES is commented out
    return []


def get_real_trades_data(ticker: str = 'NVDA', days: int = 7) -> list[Trade]:
    """Get real trading data by fetching stock prices."""
    import os
    import sys
    from datetime import datetime, timedelta

    # Add trading_bench to path
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    sys.path.insert(0, project_root)

    try:
        from trading_bench.data_fetchers.stock_fetcher import fetch_price_data

        # Calculate date range
        end_date = datetime.now() - timedelta(days=1)  # Yesterday
        start_date = end_date - timedelta(days=days)

        # Fetch real stock data
        price_data = fetch_price_data(
            ticker=ticker,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=(end_date + timedelta(days=1)).strftime('%Y-%m-%d'),
            resolution='D',
        )
        if not price_data:
            print('No price data available for the specified ticker and date range.')
            return []

        # Convert price data to trade records
        trades = []
        dates = sorted(price_data.keys())

        for i, date_str in enumerate(dates):
            if i < len(dates) - 1:  # Need next day for profit calculation
                data = price_data[date_str]
                next_data = price_data[dates[i + 1]]

                # Simple trading logic: buy if price went up next day
                trade_type = (
                    TradeType.BUY
                    if next_data['close'] > data['close']
                    else TradeType.SELL
                )

                # Calculate profit (simplified)
                if trade_type == TradeType.BUY:
                    profit = (
                        next_data['close'] - data['close']
                    ) * 100  # Assume 100 shares
                else:
                    profit = (
                        data['close'] - next_data['close']
                    ) * 100  # Profit from selling

                trade = Trade(
                    id=str(i + 1),
                    timestamp=datetime.fromisoformat(date_str),
                    symbol=ticker.upper(),
                    type=trade_type,
                    amount=100,  # Fixed 100 shares
                    price=data['close'],
                    profit=profit,
                    model='Real Data Model',
                )
                trades.append(trade)

        return trades

    except Exception as e:
        print(f'Error fetching real trades: {e}')
        return []


def get_news_data() -> list[NewsItem]:
    """Get news data."""
    return []


def get_real_news_data(query: str = 'stock market', days: int = 7) -> list[NewsItem]:
    """Get real news data from Google News."""
    import os
    import sys
    from datetime import datetime, timedelta

    # Add trading_bench to path
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    sys.path.insert(0, project_root)

    try:
        from trading_bench.data_fetchers.news_fetcher import fetch_news_data

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Fetch real news data
        raw_news = fetch_news_data(
            query=query,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            max_pages=3,
        )

        # Convert to NewsItem format
        news_items = []
        for i, article in enumerate(raw_news[:20]):  # Limit to 20 articles
            try:
                # Parse date or use current time
                try:
                    # Try to parse various date formats
                    if 'ago' in article.get('date', ''):
                        published_at = datetime.now() - timedelta(hours=1)
                    else:
                        published_at = datetime.now()
                except:
                    published_at = datetime.now()

                # Determine impact based on keywords
                title_lower = article.get('title', '').lower()
                snippet_lower = article.get('snippet', '').lower()

                if any(
                    word in title_lower or word in snippet_lower
                    for word in [
                        'crash',
                        'surge',
                        'breaking',
                        'major',
                        'federal',
                        'rate',
                    ]
                ):
                    impact = NewsImpact.HIGH
                elif any(
                    word in title_lower or word in snippet_lower
                    for word in ['rises', 'falls', 'earnings', 'report']
                ):
                    impact = NewsImpact.MEDIUM
                else:
                    impact = NewsImpact.LOW

                # Determine category based on keywords
                if any(
                    word in title_lower or word in snippet_lower
                    for word in ['fed', 'federal', 'rate', 'inflation', 'economy']
                ):
                    category = NewsCategory.ECONOMIC
                elif any(
                    word in title_lower or word in snippet_lower
                    for word in [
                        'tech',
                        'ai',
                        'software',
                        'apple',
                        'google',
                        'microsoft',
                    ]
                ):
                    category = NewsCategory.TECH
                elif any(
                    word in title_lower or word in snippet_lower
                    for word in ['earnings', 'company', 'ceo', 'revenue']
                ):
                    category = NewsCategory.COMPANY
                else:
                    category = NewsCategory.MARKET

                news_item = NewsItem(
                    id=str(i + 1),
                    title=article.get('title', 'No title'),
                    summary=article.get('snippet', 'No summary'),
                    source=article.get('source', 'Unknown'),
                    published_at=published_at,
                    impact=impact,
                    category=category,
                    url=article.get('link', '#'),
                )
                news_items.append(news_item)

            except Exception as e:
                print(f'Error processing article {i}: {e}')
                continue

        return news_items

    except Exception as e:
        print(f'Error fetching real news: {e}')
        # Fallback to sample data
        return []

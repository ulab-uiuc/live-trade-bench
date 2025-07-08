import random
from datetime import datetime, timedelta

from app.schemas import (ModelStatus, NewsCategory, NewsImpact, NewsItem,
                         Trade, TradeType, TradingModel)

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

# Sample trading history data
SAMPLE_TRADES: list[Trade] = [
    Trade(
        id='1',
        timestamp=datetime.now() - timedelta(minutes=5),
        symbol='AAPL',
        type=TradeType.SELL,
        amount=100,
        price=185.50,
        profit=150.75,
        model='LSTM Deep Learning',
    ),
    Trade(
        id='2',
        timestamp=datetime.now() - timedelta(minutes=15),
        symbol='GOOGL',
        type=TradeType.BUY,
        amount=25,
        price=2750.25,
        profit=-45.30,
        model='Random Forest',
    ),
    Trade(
        id='3',
        timestamp=datetime.now() - timedelta(minutes=30),
        symbol='MSFT',
        type=TradeType.SELL,
        amount=75,
        price=335.80,
        profit=89.25,
        model='Neural Network',
    ),
    Trade(
        id='4',
        timestamp=datetime.now() - timedelta(minutes=45),
        symbol='TSLA',
        type=TradeType.BUY,
        amount=50,
        price=245.60,
        profit=220.50,
        model='XGBoost',
    ),
    Trade(
        id='5',
        timestamp=datetime.now() - timedelta(minutes=60),
        symbol='AMZN',
        type=TradeType.SELL,
        amount=30,
        price=3380.75,
        profit=-125.80,
        model='LSTM Deep Learning',
    ),
    Trade(
        id='6',
        timestamp=datetime.now() - timedelta(minutes=90),
        symbol='NVDA',
        type=TradeType.BUY,
        amount=40,
        price=890.25,
        profit=345.60,
        model='Neural Network',
    ),
    Trade(
        id='7',
        timestamp=datetime.now() - timedelta(minutes=120),
        symbol='META',
        type=TradeType.SELL,
        amount=60,
        price=485.30,
        profit=-78.95,
        model='Random Forest',
    ),
    Trade(
        id='8',
        timestamp=datetime.now() - timedelta(minutes=150),
        symbol='NFLX',
        type=TradeType.BUY,
        amount=35,
        price=625.40,
        profit=156.75,
        model='XGBoost',
    ),
]

# Sample news data
SAMPLE_NEWS: list[NewsItem] = [
    NewsItem(
        id='1',
        title='Federal Reserve Signals Potential Interest Rate Changes',
        summary='Fed officials hint at possible rate adjustments in response to inflation data, potentially impacting market volatility and trading strategies.',
        source='Financial Times',
        published_at=datetime.now() - timedelta(minutes=30),
        impact=NewsImpact.HIGH,
        category=NewsCategory.ECONOMIC,
        url='https://example.com/news/1',
    ),
    NewsItem(
        id='2',
        title='Tech Stocks Rally on AI Breakthrough Announcements',
        summary='Major technology companies announce significant AI advancements, driving sector-wide gains and increased algorithmic trading activity.',
        source='Reuters',
        published_at=datetime.now() - timedelta(hours=1),
        impact=NewsImpact.HIGH,
        category=NewsCategory.TECH,
        url='https://example.com/news/2',
    ),
    NewsItem(
        id='3',
        title='Oil Prices Surge Following Geopolitical Tensions',
        summary='Energy commodities see significant price movements amid international developments, affecting related equity positions.',
        source='Bloomberg',
        published_at=datetime.now() - timedelta(hours=1, minutes=30),
        impact=NewsImpact.MEDIUM,
        category=NewsCategory.MARKET,
        url='https://example.com/news/3',
    ),
    NewsItem(
        id='4',
        title='Quarterly Earnings Beat Expectations for Major Banks',
        summary='Financial sector shows strong performance in latest earnings reports, with several institutions exceeding analyst projections.',
        source='Wall Street Journal',
        published_at=datetime.now() - timedelta(hours=2),
        impact=NewsImpact.MEDIUM,
        category=NewsCategory.COMPANY,
        url='https://example.com/news/4',
    ),
    NewsItem(
        id='5',
        title='Consumer Confidence Index Reaches New High',
        summary='Latest economic indicators show improved consumer sentiment, potentially signaling increased spending and market optimism.',
        source='MarketWatch',
        published_at=datetime.now() - timedelta(hours=3),
        impact=NewsImpact.MEDIUM,
        category=NewsCategory.ECONOMIC,
        url='https://example.com/news/5',
    ),
    NewsItem(
        id='6',
        title='Cryptocurrency Market Experiences Volatility',
        summary='Digital assets show mixed performance as regulatory news and institutional adoption continue to influence trading patterns.',
        source='CoinDesk',
        published_at=datetime.now() - timedelta(hours=4),
        impact=NewsImpact.LOW,
        category=NewsCategory.MARKET,
        url='https://example.com/news/6',
    ),
    NewsItem(
        id='7',
        title='Supply Chain Disruptions Affect Manufacturing Stocks',
        summary='Industrial companies report challenges in logistics and materials, leading to adjusted forecasts and trading algorithm adaptations.',
        source='Financial Times',
        published_at=datetime.now() - timedelta(hours=5),
        impact=NewsImpact.MEDIUM,
        category=NewsCategory.COMPANY,
        url='https://example.com/news/7',
    ),
    NewsItem(
        id='8',
        title='Green Energy Investments Reach Record Levels',
        summary='Renewable energy sector attracts significant capital inflows, with new projects and partnerships driving stock performance.',
        source='Reuters',
        published_at=datetime.now() - timedelta(hours=6),
        impact=NewsImpact.LOW,
        category=NewsCategory.MARKET,
        url='https://example.com/news/8',
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
    return SAMPLE_TRADES


def get_news_data() -> list[NewsItem]:
    """Get news data."""
    return SAMPLE_NEWS

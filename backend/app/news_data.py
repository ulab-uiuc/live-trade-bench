import json
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.app.config import NEWS_DATA_FILE
from live_trade_bench.systems import (
    PolymarketPortfolioSystem,
    StockPortfolioSystem,
)

def update_news_data() -> None:
    print("📰 Updating news data by calling core systems...")
    
    all_news_data = {"stock": [], "polymarket": []}

    try:
        stock_system = StockPortfolioSystem.get_instance()
        polymarket_system = PolymarketPortfolioSystem.get_instance()

        stock_market_data = stock_system._fetch_market_data()
        polymarket_market_data = polymarket_system._fetch_market_data()

        stock_news = stock_system._fetch_news_data(stock_market_data, for_date=None)
        polymarket_news = polymarket_system._fetch_news_data(polymarket_market_data, for_date=None)

        all_news_data["stock"] = [item for sublist in stock_news.values() for item in sublist]
        all_news_data["polymarket"] = [item for sublist in polymarket_news.values() for item in sublist]

        with open(NEWS_DATA_FILE, "w") as f:
            json.dump(all_news_data, f, indent=4)
        print(f"✅ News data updated and saved to {NEWS_DATA_FILE}")

    except Exception as e:
        print(f"❌ Error updating news data: {e}")

if __name__ == "__main__":
    update_news_data()

import json

from .config import NEWS_DATA_FILE


def update_news_data() -> None:
    print("📰 Updating news data...")

    all_news_data = {"stock": [], "polymarket": [], "bitmex": []}

    try:
        from .main import get_bitmex_system, get_polymarket_system, get_stock_system

        stock_system = get_stock_system()
        polymarket_system = get_polymarket_system()
        bitmex_system = get_bitmex_system()

        if not stock_system or not polymarket_system or not bitmex_system:
            print("❌ Failed to get system instances")
            return

        # Initialize systems if not already done
        if not stock_system.universe:
            stock_system.initialize_for_live()
        if not polymarket_system.universe:
            polymarket_system.initialize_for_live()
        if not bitmex_system.universe:
            bitmex_system.initialize_for_live()

        # Fetch market data
        stock_market_data = stock_system._fetch_market_data(for_date=None)
        polymarket_market_data = polymarket_system._fetch_market_data(for_date=None)
        bitmex_market_data = bitmex_system._fetch_market_data(for_date=None)

        # Fetch news data
        stock_news = stock_system._fetch_news_data(stock_market_data, for_date=None)
        polymarket_news = polymarket_system._fetch_news_data(
            polymarket_market_data, for_date=None
        )
        bitmex_news = bitmex_system._fetch_news_data(bitmex_market_data, for_date=None)

        all_news_data["stock"] = [
            item for sublist in stock_news.values() for item in sublist
        ]
        all_news_data["polymarket"] = [
            item for sublist in polymarket_news.values() for item in sublist
        ]
        all_news_data["bitmex"] = [
            item for sublist in bitmex_news.values() for item in sublist
        ]

        with open(NEWS_DATA_FILE, "w") as f:
            json.dump(all_news_data, f, indent=4)
        print(f"✅ News data updated and saved to {NEWS_DATA_FILE}")

    except Exception as e:
        print(f"❌ Error updating news data: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    update_news_data()

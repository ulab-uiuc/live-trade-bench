import json

from live_trade_bench.systems import PolymarketPortfolioSystem, StockPortfolioSystem

from .config import SOCIAL_DATA_FILE


def update_social_data() -> None:
    print("📰 Updating social media data by calling core systems...")

    all_social_data = {"stock": [], "polymarket": []}

    try:
        stock_system = StockPortfolioSystem.get_instance()
        polymarket_system = PolymarketPortfolioSystem.get_instance()

        # Initialize systems if not already done
        if not stock_system.universe:
            stock_system.initialize_for_live()
        if not polymarket_system.universe:
            polymarket_system.initialize_for_live()

        stock_social = stock_system._fetch_social_data()
        polymarket_social = polymarket_system._fetch_social_data()

        all_social_data["stock"] = [
            item for sublist in stock_social.values() for item in sublist
        ]
        all_social_data["polymarket"] = [
            item for sublist in polymarket_social.values() for item in sublist
        ]

        with open(SOCIAL_DATA_FILE, "w") as f:
            json.dump(all_social_data, f, indent=4)
        print(f"✅ Social media data updated and saved to {SOCIAL_DATA_FILE}")

    except Exception as e:
        print(f"❌ Error updating social media data: {e}")


if __name__ == "__main__":
    update_social_data()

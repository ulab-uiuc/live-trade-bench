import json

from .config import SOCIAL_DATA_FILE


def update_social_data() -> None:
    print("📱 Updating social media data...")

    all_social_data = {"stock": [], "polymarket": []}

    try:
        from backend.app.main import get_polymarket_system, get_stock_system

        stock_system = get_stock_system()
        polymarket_system = get_polymarket_system()

        if not stock_system or not polymarket_system:
            print("❌ Failed to get system instances")
            return

        # Initialize systems if not already done
        if not stock_system.universe:
            stock_system.initialize_for_live()
        if not polymarket_system.universe:
            polymarket_system.initialize_for_live()

        # Fetch social data
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
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    update_social_data()

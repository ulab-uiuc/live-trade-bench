import json
from typing import Dict, List

from .config import SOCIAL_DATA_FILE


def update_social_data() -> None:
    print("📱 Updating social media data...")

    all_social_data: Dict[str, List[Dict]] = {"stock": [], "polymarket": [], "bitmex": []}

    try:
        from .main import (  # Import system getters
            get_bitmex_system,
            get_polymarket_system,
            get_stock_system,
        )

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

        # Fetch social data using system methods
        print("  - Fetching stock social media data...")
        stock_social = stock_system._fetch_social_data()
        print(
            f"  - Fetched {len([item for sublist in stock_social.values() for item in sublist])} stock social media posts."
        )

        print("  - Fetching polymarket social media data...")
        polymarket_social = polymarket_system._fetch_social_data()
        print(
            f"  - Fetched {len([item for sublist in polymarket_social.values() for item in sublist])} polymarket social media posts."
        )

        print("  - Fetching bitmex social media data...")
        bitmex_social = bitmex_system._fetch_social_data()
        print(
            f"  - Fetched {len([item for sublist in bitmex_social.values() for item in sublist])} bitmex social media posts."
        )

        all_social_data["stock"] = [
            item for sublist in stock_social.values() for item in sublist
        ]
        all_social_data["polymarket"] = [
            item for sublist in polymarket_social.values() for item in sublist
        ]
        all_social_data["bitmex"] = [
            item for sublist in bitmex_social.values() for item in sublist
        ]

    except Exception as e:
        print(f"❌ Error updating social media data: {e}")
        import traceback

        traceback.print_exc()

    with open(SOCIAL_DATA_FILE, "w") as f:
        json.dump(all_social_data, f, indent=4)


if __name__ == "__main__":
    update_social_data()

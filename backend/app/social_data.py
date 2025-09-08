import json
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from live_trade_bench.systems import (
    create_polymarket_portfolio_system,
    create_stock_portfolio_system,
)
from .system_factory import get_system


def update_social_data() -> None:
    print("📰 Updating social media data by calling core systems...")

    all_social_data = {"stock": [], "polymarket": []}

    try:
        # Create fresh, mock-aware, thread-safe instances
        stock_system = get_system("stock")
        polymarket_system = get_system("polymarket")

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

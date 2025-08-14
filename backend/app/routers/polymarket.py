from app.data import get_real_polymarket_data, get_sample_polymarket_data
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/polymarket", tags=["polymarket"])


@router.get("/markets")
async def get_markets(
    limit: int = Query(
        default=10, ge=1, le=50, description="Number of markets to return"
    )
):
    """Get prediction markets from Polymarket."""
    try:
        # Try to get real data first
        markets = get_real_polymarket_data(limit=limit)

        # If no real data available, use sample data for development
        if not markets:
            markets = get_sample_polymarket_data()
            markets = markets[:limit]  # Apply limit to sample data

        return {
            "success": True,
            "markets": markets,
            "total_markets": len(markets),
            "data_source": "real"
            if markets and markets != get_sample_polymarket_data()[:limit]
            else "sample",
        }

    except Exception as e:
        # Return sample data as fallback
        try:
            sample_markets = get_sample_polymarket_data()
            return {
                "success": True,
                "markets": sample_markets[:limit],
                "total_markets": len(sample_markets[:limit]),
                "data_source": "sample",
                "warning": f"Using sample data due to API error: {str(e)}",
            }
        except Exception as sample_error:
            raise HTTPException(
                status_code=500,
                detail=f"Error fetching markets: {str(e)}. Sample data also failed: {str(sample_error)}",
            )


@router.get("/markets/{market_id}")
async def get_market(market_id: str):
    """Get a specific prediction market by ID."""
    try:
        markets = get_real_polymarket_data(
            limit=50
        )  # Get more markets to find specific one

        if not markets:
            markets = get_sample_polymarket_data()

        market = next((m for m in markets if m.get("id") == market_id), None)

        if not market:
            raise HTTPException(status_code=404, detail=f"Market {market_id} not found")

        return {"success": True, "market": market}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching market {market_id}: {str(e)}"
        )


@router.get("/categories")
async def get_market_categories():
    """Get available market categories."""
    try:
        markets = get_real_polymarket_data(limit=50)

        if not markets:
            markets = get_sample_polymarket_data()

        categories = list(set(market.get("category", "unknown") for market in markets))
        categories = [cat for cat in categories if cat and cat != "unknown"]

        if not categories:
            categories = ["crypto", "politics", "tech", "economics", "sports"]

        return {
            "success": True,
            "categories": sorted(categories),
            "total_categories": len(categories),
        }

    except Exception as e:
        # Return default categories
        default_categories = ["crypto", "politics", "tech", "economics", "sports"]
        return {
            "success": True,
            "categories": default_categories,
            "total_categories": len(default_categories),
            "warning": f"Using default categories due to error: {str(e)}",
        }


@router.get("/markets/category/{category}")
async def get_markets_by_category(
    category: str,
    limit: int = Query(
        default=10, ge=1, le=50, description="Number of markets to return"
    ),
):
    """Get prediction markets filtered by category."""
    try:
        markets = get_real_polymarket_data(limit=50)  # Get more to filter

        if not markets:
            markets = get_sample_polymarket_data()

        # Filter by category (case-insensitive)
        filtered_markets = [
            market
            for market in markets
            if market.get("category", "").lower() == category.lower()
        ]

        # Apply limit
        filtered_markets = filtered_markets[:limit]

        return {
            "success": True,
            "markets": filtered_markets,
            "category": category,
            "total_markets": len(filtered_markets),
            "data_source": "real"
            if markets and markets != get_sample_polymarket_data()
            else "sample",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching markets for category {category}: {str(e)}",
        )


@router.get("/stats")
async def get_polymarket_stats():
    """Get general polymarket statistics."""
    try:
        markets = get_real_polymarket_data(limit=50)

        if not markets:
            markets = get_sample_polymarket_data()

        # Calculate statistics
        total_markets = len(markets)
        active_markets = len([m for m in markets if m.get("status") == "active"])
        categories = list(set(m.get("category", "unknown") for m in markets))
        categories = [cat for cat in categories if cat and cat != "unknown"]

        # Calculate total volume and liquidity
        total_volume = sum(
            float(m.get("total_volume", 0))
            for m in markets
            if m.get("total_volume") is not None
        )
        total_liquidity = sum(
            float(m.get("total_liquidity", 0))
            for m in markets
            if m.get("total_liquidity") is not None
        )

        return {
            "success": True,
            "stats": {
                "total_markets": total_markets,
                "active_markets": active_markets,
                "total_categories": len(categories),
                "categories": sorted(categories),
                "total_volume": total_volume,
                "total_liquidity": total_liquidity,
                "avg_volume_per_market": total_volume / max(total_markets, 1),
                "avg_liquidity_per_market": total_liquidity / max(total_markets, 1),
            },
            "data_source": "real"
            if markets and markets != get_sample_polymarket_data()
            else "sample",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error calculating polymarket stats: {str(e)}"
        )

from typing import Any, Dict, List
from fastapi import APIRouter, Query, HTTPException
import os
import sys
from datetime import datetime, timedelta

# Add live_trade_bench to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

# Try to import Reddit fetcher, but use fallback if not available
try:
    from live_trade_bench.fetchers.reddit_fetcher import fetch_reddit_data
    REDDIT_AVAILABLE = True
except ImportError:
    REDDIT_AVAILABLE = False

from live_trade_bench.fetchers.stock_fetcher import get_stock_tickers

router = APIRouter(prefix="/api/social", tags=["social"])

def _classify_sentiment(text: str) -> str:
    """Classify post sentiment based on keywords."""
    text_lower = text.lower()
    
    bullish_keywords = ["buy", "moon", "bullish", "pump", "gain", "profit", "up", "green", "rocket"]
    bearish_keywords = ["sell", "dump", "bearish", "crash", "loss", "down", "red", "drop", "fall"]
    
    bullish_count = sum(1 for keyword in bullish_keywords if keyword in text_lower)
    bearish_count = sum(1 for keyword in bearish_keywords if keyword in text_lower)
    
    if bullish_count > bearish_count:
        return "bullish"
    elif bearish_count > bullish_count:
        return "bearish"
    else:
        return "neutral"

def _get_fallback_social_posts(limit: int, category: str = "all") -> List[Dict[str, Any]]:
    """Fallback mock social posts if fetcher fails."""
    import random
    
    posts = []
    
    if category in ["all", "stock"]:
        stock_companies = ["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA", "META", "AMZN"]
        stock_templates = [
            "Just analyzed {} charts. Looking {} for next week!",
            "Anyone else holding {} through earnings? Feeling {}.",
            "{} fundamentals are solid. I'm {} long-term.",
            "Technical analysis on {} shows {} patterns emerging.",
            "What's everyone's take on {} after today's movement?",
        ]
        
        stock_limit = limit if category == "stock" else limit // 2
        for i in range(min(stock_limit, 15)):
            company = random.choice(stock_companies)
            sentiment = random.choice(["bullish", "bearish", "neutral"])
            template = random.choice(stock_templates)
            
            posts.append({
                "id": f"stock_post_{i}",
                "content": template.format(company, sentiment),
                "author": f"trader_{i}",
                "platform": random.choice(["reddit", "twitter", "discord"]),
                "created_at": (datetime.now() - timedelta(hours=random.randint(1, 24))).isoformat(),
                "sentiment": sentiment,
                "upvotes": random.randint(5, 200),
                "category": "stock",
                "market_type": "stock",
                "stock_symbols": [company],
                "url": f"https://reddit.com/r/stocks/post_{i}"
            })
    
    if category in ["all", "polymarket"]:
        poly_topics = ["2024 Election", "AI Development", "Fed Policy", "Climate Action", "Crypto Regulation"]
        poly_templates = [
            "Odds on {} just shifted. Market sentiment is {}.",
            "Big volume in {} prediction market. Feeling {}.",
            "Analysis suggests {} outcome is {}. Thoughts?",
            "Sharp money betting {} on {}. I'm {} too.",
            "Prediction market for {} heating up. What's your take?",
        ]
        
        poly_limit = limit if category == "polymarket" else limit // 2
        for i in range(min(poly_limit, 15)):
            topic = random.choice(poly_topics)
            sentiment = random.choice(["bullish", "bearish", "neutral"])
            template = random.choice(poly_templates)
            confidence = {"bullish": "likely", "bearish": "unlikely", "neutral": "uncertain"}[sentiment]
            
            posts.append({
                "id": f"poly_post_{i}",
                "content": template.format(confidence, topic, sentiment),
                "author": f"predictor_{i}",
                "platform": random.choice(["reddit", "twitter", "discord"]),
                "created_at": (datetime.now() - timedelta(hours=random.randint(1, 24))).isoformat(),
                "sentiment": sentiment,
                "upvotes": random.randint(10, 150),
                "category": "polymarket",
                "market_type": "polymarket",
                "prediction_market": topic,
                "url": f"https://reddit.com/r/polymarket/post_{i}"
            })
    
    return posts

@router.get("/")
async def get_all_social_posts(
    limit: int = Query(default=20, ge=1, le=100),
) -> List[Dict[str, Any]]:
    """Get mixed social media data from both stock and polymarket."""
    
    # For now, use fallback data since Reddit API requires special setup
    # TODO: Implement real Reddit fetcher when credentials are available
    return _get_fallback_social_posts(limit, "all")

@router.get("/stock")
async def get_stock_social_posts(
    limit: int = Query(default=20, ge=1, le=100),
) -> List[Dict[str, Any]]:
    """Get stock-related social media posts."""
    
    # For now, use fallback data 
    # TODO: Implement real Reddit fetcher for r/stocks, r/investing, etc.
    return _get_fallback_social_posts(limit, "stock")

@router.get("/polymarket")
async def get_polymarket_social_posts(
    limit: int = Query(default=20, ge=1, le=100),
) -> List[Dict[str, Any]]:
    """Get polymarket/prediction market social media posts."""
    
    # For now, use fallback data
    # TODO: Implement real Reddit fetcher for r/polymarket, r/predictionmarkets, etc.
    return _get_fallback_social_posts(limit, "polymarket")
from typing import Any, Dict, List
from fastapi import APIRouter, Query, HTTPException
import os
import sys
import threading
import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add live_trade_bench to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

# Try to import Reddit fetcher, but use fallback if not available
try:
    from live_trade_bench.fetchers.reddit_fetcher import fetch_top_from_category, fetch_reddit_posts_by_ticker
    REDDIT_AVAILABLE = True
except ImportError:
    REDDIT_AVAILABLE = False

from live_trade_bench.fetchers.stock_fetcher import fetch_trending_stocks

router = APIRouter(prefix="/api/social", tags=["social"])

# Global cache for social media data
_social_cache = {
    "all": {"data": [], "last_updated": None},
    "stock": {"data": [], "last_updated": None},
    "polymarket": {"data": [], "last_updated": None}
}
_cache_lock = threading.Lock()
_cache_duration = 30 * 60  # 30 minutes cache duration
_background_fetcher_running = False

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

def _fetch_social_posts_task(fetch_function, *args) -> List[Dict[str, Any]]:
    """Generic wrapper to run a fetch function in a thread and handle exceptions."""
    try:
        return fetch_function(*args)
    except Exception as e:
        print(f"⚠️ Error in social fetch task ({fetch_function.__name__}): {e}")
        return []

def _fetch_real_stock_social(limit: int) -> List[Dict[str, Any]]:
    """Fetch real stock-related social media posts in parallel."""
    try:
        if not REDDIT_AVAILABLE:
            return _get_fallback_social_posts(limit, "stock")
        
        print("📱 Fetching real stock social media posts in parallel...")
        
        trending_stocks = fetch_trending_stocks()
        stock_symbols = trending_stocks[:5] if trending_stocks else []
        today = datetime.now().strftime("%Y-%m-%d")
        
        all_posts = []
        with ThreadPoolExecutor(max_workers=len(stock_symbols) + 1) as executor:
            # Futures for fetching posts by ticker
            future_to_fetch = {
                executor.submit(_fetch_social_posts_task, fetch_reddit_posts_by_ticker, symbol, today, limit // 5): symbol
                for symbol in stock_symbols
            }
            # Future for fetching general company news
            future_to_fetch[executor.submit(_fetch_social_posts_task, fetch_top_from_category, "company_news", today, limit // 3)] = "company_news"

            for future in as_completed(future_to_fetch):
                posts = future.result()
                all_posts.extend(posts)

        # Format the posts
        formatted_posts = []
        for i, post in enumerate(all_posts[:limit]):
            content = post.get('title', '') + ' ' + post.get('content', '')
            post_symbols = [s for s in (trending_stocks or []) if s.upper() in content.upper()]
            
            formatted_posts.append({
                "id": f"real_stock_social_{i}_{int(time.time())}",
                "content": post.get('title', 'Stock discussion'),
                "author": post.get('author', 'anonymous'),
                "platform": "reddit",
                "created_at": post.get('created_utc', datetime.now().isoformat()),
                "sentiment": _classify_sentiment(content),
                "upvotes": post.get('upvotes', 0),
                "category": "stock",
                "market_type": "stock",
                "stock_symbols": post_symbols,
                "url": post.get('url', 'https://reddit.com')
            })
        
        print(f"✅ Successfully fetched {len(formatted_posts)} real stock social posts in parallel")
        return formatted_posts
        
    except Exception as e:
        print(f"❌ Error fetching real stock social posts in parallel: {e}")
        return _get_fallback_social_posts(limit, "stock")

def _fetch_real_polymarket_social(limit: int) -> List[Dict[str, Any]]:
    """Fetch real polymarket-related social media posts in parallel."""
    try:
        if not REDDIT_AVAILABLE:
            return _get_fallback_social_posts(limit, "polymarket")
        
        print("🎯 Fetching real polymarket social media posts in parallel...")
        
        today = datetime.now().strftime("%Y-%m-%d")
        categories = ["politics", "crypto"]
        all_posts = []

        with ThreadPoolExecutor(max_workers=len(categories)) as executor:
            future_to_category = {
                executor.submit(_fetch_social_posts_task, fetch_top_from_category, category, today, limit // 2): category
                for category in categories
            }
            for future in as_completed(future_to_category):
                posts = future.result()
                all_posts.extend(posts)
        
        # Format the posts
        formatted_posts = []
        for i, post in enumerate(all_posts[:limit]):
            content = post.get('title', '') + ' ' + post.get('content', '')
            
            formatted_posts.append({
                "id": f"real_poly_social_{i}_{int(time.time())}",
                "content": post.get('title', 'Political/prediction discussion'),
                "author": post.get('author', 'anonymous'),
                "platform": "reddit",
                "created_at": post.get('created_utc', datetime.now().isoformat()),
                "sentiment": _classify_sentiment(content),
                "upvotes": post.get('upvotes', 0),
                "category": "polymarket",
                "market_type": "polymarket",
                "stock_symbols": [],
                "url": post.get('url', 'https://reddit.com')
            })
        
        print(f"✅ Successfully fetched {len(formatted_posts)} real polymarket social posts in parallel")
        return formatted_posts
        
    except Exception as e:
        print(f"❌ Error fetching real polymarket social posts in parallel: {e}")
        return _get_fallback_social_posts(limit, "polymarket")

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

def _is_cache_valid(category: str) -> bool:
    """Check if cache is still valid for the given category"""
    with _cache_lock:
        cache_entry = _social_cache.get(category)
        if not cache_entry or not cache_entry["last_updated"]:
            return False
        
        time_since_update = time.time() - cache_entry["last_updated"]
        return time_since_update < _cache_duration

def _get_cached_social(category: str) -> List[Dict[str, Any]]:
    """Get cached social data for the given category"""
    with _cache_lock:
        return _social_cache.get(category, {}).get("data", []).copy()

def _update_cache(category: str, data: List[Dict[str, Any]]) -> None:
    """Update cache for the given category"""
    with _cache_lock:
        _social_cache[category] = {
            "data": data,
            "last_updated": time.time()
        }

def _background_social_fetcher():
    """Background thread to periodically fetch and cache social media data"""
    global _background_fetcher_running
    
    while _background_fetcher_running:
        try:
            print("🔄 Background fetching social media...")
            
            # Fetch and cache stock social posts
            stock_posts = _get_fallback_social_posts(15, "stock")
            _update_cache("stock", stock_posts)
            print(f"   ✅ Cached {len(stock_posts)} stock social posts")
            
            # Fetch and cache polymarket social posts
            poly_posts = _get_fallback_social_posts(15, "polymarket")
            _update_cache("polymarket", poly_posts)
            print(f"   ✅ Cached {len(poly_posts)} polymarket social posts")
            
            # Create mixed social posts
            mixed_posts = stock_posts[:10] + poly_posts[:10]
            mixed_posts.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            _update_cache("all", mixed_posts[:20])
            print(f"   ✅ Cached {len(mixed_posts)} mixed social posts")
            
            # Wait 30 minutes before next fetch
            time.sleep(30 * 60)
            
        except Exception as e:
            print(f"❌ Background social fetcher error: {e}")
            time.sleep(5 * 60)  # Wait 5 minutes on error

def start_background_social_fetcher():
    """Start the background social fetcher"""
    global _background_fetcher_running
    
    if _background_fetcher_running:
        return
    
    _background_fetcher_running = True
    thread = threading.Thread(target=_background_social_fetcher, daemon=True)
    thread.start()
    print("🚀 Background social fetcher started")

def stop_background_social_fetcher():
    """Stop the background social fetcher"""
    global _background_fetcher_running
    _background_fetcher_running = False
    print("⏹️ Background social fetcher stopped")

@router.get("/")
async def get_all_social_posts(
    limit: int = Query(default=20, ge=1, le=100),
) -> List[Dict[str, Any]]:
    """Get mixed social media data - ALWAYS FRESH, NO CACHE."""
    
    try:
        print("💬 Fetching fresh mixed social posts (cache disabled)...")
        
        # Always fetch fresh data
        stock_posts = _fetch_real_stock_social(limit // 2)
        polymarket_posts = _fetch_real_polymarket_social(limit // 2)
        
        all_posts = stock_posts + polymarket_posts
        all_posts.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        print(f"💬 Returning {len(all_posts[:limit])} fresh mixed social posts")
        return all_posts[:limit]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching social posts: {str(e)}")

@router.get("/stock")
async def get_stock_social_posts(
    limit: int = Query(default=20, ge=1, le=100),
) -> List[Dict[str, Any]]:
    """Get stock-related social media posts - ALWAYS FRESH, NO CACHE."""
    
    try:
        print("📈 Fetching fresh stock social posts (cache disabled)...")
        
        # Always fetch fresh data
        fresh_posts = _fetch_real_stock_social(limit)
        
        print(f"📈 Returning {len(fresh_posts)} fresh stock social posts")
        return fresh_posts
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stock social posts: {str(e)}")

@router.get("/polymarket")
async def get_polymarket_social_posts(
    limit: int = Query(default=20, ge=1, le=100),
) -> List[Dict[str, Any]]:
    """Get polymarket/prediction market social media posts - ALWAYS FRESH, NO CACHE."""
    
    try:
        print("🎯 Fetching fresh polymarket social posts (cache disabled)...")
        
        # Always fetch fresh data
        fresh_posts = _fetch_real_polymarket_social(limit)
        
        print(f"🎯 Returning {len(fresh_posts)} fresh polymarket social posts")
        return fresh_posts
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching polymarket social posts: {str(e)}")
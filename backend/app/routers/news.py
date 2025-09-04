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

from live_trade_bench.fetchers.news_fetcher import fetch_news_data
from live_trade_bench.fetchers.stock_fetcher import fetch_trending_stocks

router = APIRouter(prefix="/api/news", tags=["news"])

# Global cache for news data
_news_cache = {
    "all": {"data": [], "last_updated": None},
    "stock": {"data": [], "last_updated": None},
    "polymarket": {"data": [], "last_updated": None}
}
_cache_lock = threading.Lock()
_cache_duration = 30 * 60  # 30 minutes cache duration
_background_fetcher_running = False

def _classify_impact(text: str) -> str:
    """Classify news impact based on keywords."""
    text_lower = text.lower()
    
    high_impact_keywords = ["earnings", "merger", "acquisition", "breakthrough", "lawsuit", "regulatory", "fda", "approval"]
    medium_impact_keywords = ["guidance", "upgrade", "downgrade", "analyst", "revenue", "growth"]
    
    if any(keyword in text_lower for keyword in high_impact_keywords):
        return "high"
    elif any(keyword in text_lower for keyword in medium_impact_keywords):
        return "medium"
    else:
        return "low"

def _fetch_one_ticker_news(symbol: str, start_date: str, end_date: str, news_per_ticker: int) -> List[Dict[str, Any]]:
    """Fetch and format news for a single stock ticker. To be run in a thread pool."""
    try:
        print(f"  📰 Fetching news for {symbol}...")
        ticker_query = f"{symbol} stock OR {symbol} earnings OR {symbol} news"
        ticker_news = fetch_news_data(
            query=ticker_query,
            start_date=start_date,
            end_date=end_date,
            max_pages=1
        )
        
        formatted_news = []
        for i, news_item in enumerate(ticker_news[:news_per_ticker]):
            title = news_item.get('title', 'Stock Market Update')
            content = news_item.get('snippet', 'Market news update')
            
            formatted_news.append({
                "id": f"real_stock_{symbol}_{i}_{int(time.time())}",
                "title": title,
                "summary": content,
                "source": news_item.get('source', 'Financial News'),
                "published_at": news_item.get('date', datetime.now().isoformat()),
                "impact": _classify_impact(title + ' ' + content),
                "category": "stock",
                "market_type": "stock",
                "stock_symbol": symbol,
                "url": news_item.get('link', f"https://finance.yahoo.com/quote/{symbol}")
            })
        print(f"    ✅ Got {len(formatted_news)} news items for {symbol}")
        return formatted_news
    except Exception as e:
        print(f"    ❌ Error fetching news for {symbol}: {e}")
        return []

def _fetch_real_stock_news(limit: int) -> List[Dict[str, Any]]:
    """Fetch real stock news using live_trade_bench fetchers in parallel."""
    try:
        trending_stocks = fetch_trending_stocks()
        stock_symbols = trending_stocks[:10] if trending_stocks else ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
        
        print(f"📈 Fetching news in parallel for tickers: {stock_symbols[:5]}...")
        
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        all_formatted_news = []
        news_per_ticker = max(1, limit // len(stock_symbols[:5]))
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_symbol = {
                executor.submit(_fetch_one_ticker_news, symbol, start_date, end_date, news_per_ticker): symbol
                for symbol in stock_symbols[:5]
            }
            for future in as_completed(future_to_symbol):
                all_formatted_news.extend(future.result())
        
        print(f"✅ Successfully fetched {len(all_formatted_news)} real stock news items in parallel")
        return all_formatted_news
        
    except Exception as e:
        print(f"❌ Error fetching real stock news in parallel: {e}")
        import traceback
        traceback.print_exc()
        return _get_fallback_stock_news(limit)

def _fetch_one_topic_news(topic: str, start_date: str, end_date: str, news_per_topic: int) -> List[Dict[str, Any]]:
    """Fetch and format news for a single polymarket topic. To be run in a thread pool."""
    try:
        print(f"  📰 Fetching news for topic: {topic}...")
        topic_query = f"{topic} news OR {topic} prediction OR {topic} market OR {topic} polls"
        topic_news = fetch_news_data(
            query=topic_query,
            start_date=start_date,
            end_date=end_date,
            max_pages=1
        )
        
        formatted_news = []
        for i, news_item in enumerate(topic_news[:news_per_topic]):
            title = news_item.get('title', 'Prediction Market Update')
            content = news_item.get('snippet', 'Prediction market news update')
            
            formatted_news.append({
                "id": f"real_poly_{topic}_{i}_{int(time.time())}",
                "title": title,
                "summary": content,
                "source": news_item.get('source', 'Political News'),
                "published_at": news_item.get('date', datetime.now().isoformat()),
                "impact": _classify_impact(title + ' ' + content),
                "category": "polymarket",
                "market_type": "polymarket",
                "stock_symbol": None,
                "polymarket_topic": topic,
                "url": news_item.get('link', "https://polymarket.com")
            })
        print(f"    ✅ Got {len(formatted_news)} news items for {topic}")
        return formatted_news
    except Exception as e:
        print(f"    ❌ Error fetching news for {topic}: {e}")
        return []

def _fetch_real_polymarket_news(limit: int) -> List[Dict[str, Any]]:
    """Fetch real polymarket news using live_trade_bench fetchers in parallel."""
    try:
        print(f"📊 Fetching polymarket news in parallel for each topic...")
        
        try:
            from live_trade_bench.fetchers.polymarket_fetcher import fetch_trending_markets
            trending_markets = fetch_trending_markets(limit=10)
            polymarket_topics = list(set(
                term for market in trending_markets 
                for term in _extract_key_terms_from_question(market.get('question', ''))
            ))[:8]
            print(f"  🎯 Using trending topics: {polymarket_topics[:5]}...")
        except Exception as e:
            print(f"⚠️ Could not fetch trending markets: {e}")
            polymarket_topics = ["election", "politics", "federal reserve", "inflation", "AI"]
        
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        all_formatted_news = []
        news_per_topic = max(1, limit // len(polymarket_topics[:5]))
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_topic = {
                executor.submit(_fetch_one_topic_news, topic, start_date, end_date, news_per_topic): topic
                for topic in polymarket_topics[:5]
            }
            for future in as_completed(future_to_topic):
                all_formatted_news.extend(future.result())

        print(f"✅ Successfully fetched {len(all_formatted_news)} real polymarket news items in parallel")
        return all_formatted_news
        
    except Exception as e:
        print(f"❌ Error fetching real polymarket news in parallel: {e}")
        import traceback
        traceback.print_exc()
        return _get_fallback_polymarket_news(limit)

def _extract_key_terms_from_question(question: str) -> List[str]:
    """Extract key search terms from a polymarket question."""
    # Common words to exclude
    stop_words = {"will", "be", "the", "in", "on", "at", "by", "for", "to", "of", "and", "or", "a", "an"}
    
    # Split and clean
    words = question.lower().replace("?", "").split()
    key_terms = []
    
    for word in words:
        word = word.strip(".,!?()[]")
        if len(word) > 3 and word not in stop_words:
            key_terms.append(word)
    
    # Take first 3 key terms
    return key_terms[:3]

def _get_fallback_stock_news(limit: int) -> List[Dict[str, Any]]:
    """Fallback mock stock news if fetcher fails."""
    import random
    
    companies = ["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA", "META", "AMZN"]
    titles = [
        "{} reports quarterly earnings beat",
        "{} announces new product launch", 
        "{} stock price targets raised by analysts",
        "{} faces market headwinds",
        "{} shows strong revenue growth"
    ]
    
    news_items = []
    for i in range(min(limit, 10)):
        company = random.choice(companies)
        title_template = random.choice(titles)
        
        news_items.append({
            "id": f"fallback_stock_{i}",
            "title": title_template.format(company),
            "summary": f"Market update for {company} showing recent developments and analyst opinions.",
            "source": "Market News",
            "published_at": (datetime.now() - timedelta(hours=random.randint(1, 48))).isoformat(),
            "impact": random.choice(["high", "medium", "low"]),
            "category": "stock",
            "market_type": "stock",
            "stock_symbol": company,  # Add single stock symbol for frontend
            "url": f"https://example.com/news/{i}"
        })
    
    return news_items

def _get_fallback_polymarket_news(limit: int) -> List[Dict[str, Any]]:
    """Fallback mock polymarket news if fetcher fails."""
    import random
    
    topics = ["2024 Election", "AI Development", "Fed Policy", "Climate Action", "Crypto Regulation"]
    titles = [
        "{} prediction market sees increased activity",
        "Betting odds shift on {} outcome",
        "Market sentiment changes for {}",
        "New predictions emerge for {}",
        "Analysis impacts {} market odds"
    ]
    
    news_items = []
    for i in range(min(limit, 10)):
        topic = random.choice(topics)
        title_template = random.choice(titles)
        
        news_items.append({
            "id": f"fallback_poly_{i}",
            "title": title_template.format(topic),
            "summary": f"Prediction market analysis for {topic} with updated odds and trading volume.",
            "source": "Prediction Markets Daily",
            "published_at": (datetime.now() - timedelta(hours=random.randint(1, 48))).isoformat(),
            "impact": random.choice(["high", "medium", "low"]),
            "category": "polymarket",
            "market_type": "polymarket",
            "prediction_market": topic,
            "url": f"https://example.com/poly/{i}"
        })
    
    return news_items

def _is_cache_valid(category: str) -> bool:
    """Check if cache is still valid for the given category"""
    with _cache_lock:
        cache_entry = _news_cache.get(category)
        if not cache_entry or not cache_entry["last_updated"]:
            return False
        
        time_since_update = time.time() - cache_entry["last_updated"]
        return time_since_update < _cache_duration

def _get_cached_news(category: str) -> List[Dict[str, Any]]:
    """Get cached news for the given category"""
    with _cache_lock:
        return _news_cache.get(category, {}).get("data", []).copy()

def _update_cache(category: str, data: List[Dict[str, Any]]) -> None:
    """Update cache for the given category"""
    with _cache_lock:
        _news_cache[category] = {
            "data": data,
            "last_updated": time.time()
        }

def _background_news_fetcher():
    """Background thread to periodically fetch and cache news"""
    global _background_fetcher_running
    
    while _background_fetcher_running:
        try:
            print("🔄 Background fetching news...")
            
            # Fetch and cache stock news using real fetcher
            stock_news = _fetch_real_stock_news(15)
            _update_cache("stock", stock_news)
            print(f"   ✅ Cached {len(stock_news)} stock news")
            
            # Fetch and cache polymarket news using real fetcher
            poly_news = _fetch_real_polymarket_news(15)
            _update_cache("polymarket", poly_news)
            print(f"   ✅ Cached {len(poly_news)} polymarket news")
            
            # Create mixed news
            mixed_news = stock_news[:10] + poly_news[:10]
            mixed_news.sort(key=lambda x: x.get("published_at", ""), reverse=True)
            _update_cache("all", mixed_news[:20])
            print(f"   ✅ Cached {len(mixed_news)} mixed news")
            
            # Wait 30 minutes before next fetch
            time.sleep(30 * 60)
            
        except Exception as e:
            print(f"❌ Background news fetcher error: {e}")
            time.sleep(5 * 60)  # Wait 5 minutes on error

def start_background_news_fetcher():
    """Start the background news fetcher"""
    global _background_fetcher_running
    
    if _background_fetcher_running:
        return
    
    _background_fetcher_running = True
    thread = threading.Thread(target=_background_news_fetcher, daemon=True)
    thread.start()
    print("🚀 Background news fetcher started")

def stop_background_news_fetcher():
    """Stop the background news fetcher"""
    global _background_fetcher_running
    _background_fetcher_running = False
    print("⏹️ Background news fetcher stopped")

@router.get("/")
async def get_all_news(
    limit: int = Query(default=20, ge=1, le=100),
) -> List[Dict[str, Any]]:
    """Get mixed news data - ALWAYS FRESH, NO CACHE."""
    
    try:
        print("📰 Fetching fresh mixed news (cache disabled)...")
        
        # Always fetch fresh data
        stock_news = _fetch_real_stock_news(limit // 2)
        poly_news = _fetch_real_polymarket_news(limit // 2)
        
        all_news = stock_news + poly_news
        all_news.sort(key=lambda x: x.get("published_at", ""), reverse=True)
        
        print(f"📰 Returning {len(all_news[:limit])} fresh mixed news items")
        return all_news[:limit]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching news: {str(e)}")


@router.get("/stock")
async def get_stock_news(
    limit: int = Query(default=20, ge=1, le=100),
) -> List[Dict[str, Any]]:
    """Get stock-related news - ALWAYS FRESH, NO CACHE."""
    
    try:
        print("📈 Fetching fresh stock news (cache disabled)...")
        
        # Always fetch fresh data
        fresh_news = _fetch_real_stock_news(limit)
        
        print(f"📈 Returning {len(fresh_news)} fresh stock news items")
        return fresh_news
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stock news: {str(e)}")


@router.get("/polymarket")
async def get_polymarket_news(
    limit: int = Query(default=20, ge=1, le=100),
) -> List[Dict[str, Any]]:
    """Get polymarket/prediction market news - ALWAYS FRESH, NO CACHE."""
    
    try:
        print("🎯 Fetching fresh polymarket news (cache disabled)...")
        
        # Always fetch fresh data
        fresh_news = _fetch_real_polymarket_news(limit)
        
        print(f"🎯 Returning {len(fresh_news)} fresh polymarket news items")
        return fresh_news
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching polymarket news: {str(e)}")


@router.post("/clear-cache")
async def clear_news_cache() -> Dict[str, str]:
    """Clear all news cache to force fresh data fetch."""
    global _news_cache
    
    with _cache_lock:
        _news_cache = {
            "all": {"data": [], "last_updated": None},
            "stock": {"data": [], "last_updated": None}, 
            "polymarket": {"data": [], "last_updated": None}
        }
    
    print("🗑️ News cache cleared! Next requests will fetch fresh data.")
    return {"status": "Cache cleared successfully"}
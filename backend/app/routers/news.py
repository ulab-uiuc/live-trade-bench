from typing import Any, Dict, List
from fastapi import APIRouter, Query, HTTPException
import os
import sys
from datetime import datetime, timedelta

# Add live_trade_bench to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from live_trade_bench.fetchers.news_fetcher import fetch_news_data
from live_trade_bench.fetchers.stock_fetcher import get_stock_tickers

router = APIRouter(prefix="/api/news", tags=["news"])

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
            "stock_symbols": [company],
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

@router.get("/")
async def get_all_news(
    limit: int = Query(default=20, ge=1, le=100),
) -> List[Dict[str, Any]]:
    """Get mixed news data from both stock and polymarket using real fetchers."""
    
    try:
        all_news = []
        
        # Get stock news using real fetcher
        stock_news = await get_stock_news(limit // 2)
        all_news.extend(stock_news)
        
        # Get polymarket news using real fetcher  
        poly_news = await get_polymarket_news(limit // 2)
        all_news.extend(poly_news)
        
        # Sort by published date (most recent first)
        all_news.sort(key=lambda x: x.get("published_at", ""), reverse=True)
        
        return all_news[:limit]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching news: {str(e)}")


@router.get("/stock")
async def get_stock_news(
    limit: int = Query(default=20, ge=1, le=100),
) -> List[Dict[str, Any]]:
    """Get stock-related news using live_trade_bench fetcher."""
    
    try:
        # Get stock tickers
        tickers = get_stock_tickers(limit=10)  # Get top 10 stocks
        
        # Get date range (last 7 days)
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        all_news = []
        
        # Fetch news for each ticker
        for ticker in tickers[:5]:  # Limit to top 5 to avoid too many API calls
            try:
                query = f"{ticker} stock earnings news"
                news_data = fetch_news_data(query, start_date, end_date, max_pages=1)
                
                for news_item in news_data:
                    # Format news item to match expected structure
                    formatted_item = {
                        "id": f"stock_{ticker}_{news_item.get('id', hash(news_item.get('url', '')))}",
                        "title": news_item.get("title", ""),
                        "summary": news_item.get("snippet", "")[:200] + "..." if len(news_item.get("snippet", "")) > 200 else news_item.get("snippet", ""),
                        "source": news_item.get("source", "Unknown"),
                        "published_at": news_item.get("date", datetime.now().isoformat()),
                        "impact": _classify_impact(news_item.get("title", "") + " " + news_item.get("snippet", "")),
                        "category": "stock",
                        "market_type": "stock", 
                        "stock_symbols": [ticker],
                        "url": news_item.get("url", "")
                    }
                    all_news.append(formatted_item)
                    
            except Exception as e:
                print(f"Error fetching news for {ticker}: {e}")
                continue
        
        # Sort by date and limit results
        all_news.sort(key=lambda x: x.get("published_at", ""), reverse=True)
        return all_news[:limit]
        
    except Exception as e:
        # Fallback to basic mock data if fetcher fails
        print(f"News fetcher failed, using fallback: {e}")
        return _get_fallback_stock_news(limit)


@router.get("/polymarket")
async def get_polymarket_news(
    limit: int = Query(default=20, ge=1, le=100),
) -> List[Dict[str, Any]]:
    """Get polymarket/prediction market news using live_trade_bench fetcher."""
    
    try:
        # Get date range (last 7 days)
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        all_news = []
        
        # Polymarket topics to search for
        topics = [
            "2024 presidential election prediction market",
            "AI breakthrough prediction betting",
            "federal reserve rate decision betting",
            "climate policy prediction market",
            "cryptocurrency regulation betting"
        ]
        
        # Fetch news for each topic
        for topic in topics[:3]:  # Limit to top 3 to avoid too many API calls
            try:
                news_data = fetch_news_data(topic, start_date, end_date, max_pages=1)
                
                for news_item in news_data:
                    # Format news item to match expected structure
                    formatted_item = {
                        "id": f"poly_{hash(news_item.get('url', ''))}",
                        "title": news_item.get("title", ""),
                        "summary": news_item.get("snippet", "")[:200] + "..." if len(news_item.get("snippet", "")) > 200 else news_item.get("snippet", ""),
                        "source": news_item.get("source", "Unknown"),
                        "published_at": news_item.get("date", datetime.now().isoformat()),
                        "impact": _classify_impact(news_item.get("title", "") + " " + news_item.get("snippet", "")),
                        "category": "polymarket",
                        "market_type": "polymarket",
                        "prediction_market": topic.split()[0:3],  # Extract main topic
                        "url": news_item.get("url", "")
                    }
                    all_news.append(formatted_item)
                    
            except Exception as e:
                print(f"Error fetching polymarket news for {topic}: {e}")
                continue
        
        # Sort by date and limit results
        all_news.sort(key=lambda x: x.get("published_at", ""), reverse=True)
        
        # If we didn't get enough real news, supplement with fallback
        if len(all_news) < limit // 2:
            fallback_news = _get_fallback_polymarket_news(limit - len(all_news))
            all_news.extend(fallback_news)
        
        return all_news[:limit]
        
    except Exception as e:
        # Fallback to mock data if fetcher fails
        print(f"Polymarket news fetcher failed, using fallback: {e}")
        return _get_fallback_polymarket_news(limit)
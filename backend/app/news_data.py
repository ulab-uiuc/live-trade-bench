"""
News data provider using live_trade_bench fetchers
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add live_trade_bench to path
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, project_root)

from live_trade_bench.fetchers.news_fetcher import NewsFetcher

# Company name mapping for ticker symbols
TICKER_TO_COMPANY = {
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "GOOGL": "Google",
    "AMZN": "Amazon",
    "TSLA": "Tesla",
    "NVDA": "Nvidia",
    "TSM": "Taiwan Semiconductor Manufacturing Company OR TSMC",
    "JPM": "JPMorgan Chase OR JP Morgan",
    "JNJ": "Johnson & Johnson OR JNJ",
    "V": "Visa",
    "WMT": "Walmart",
    "META": "Meta OR Facebook",
    "AMD": "AMD",
    "INTC": "Intel",
    "QCOM": "Qualcomm",
    "BABA": "Alibaba",
    "ADBE": "Adobe",
    "NFLX": "Netflix",
    "CRM": "Salesforce",
    "PYPL": "PayPal",
    "PLTR": "Palantir",
    "MU": "Micron",
    "SQ": "Block OR Square",
    "ZM": "Zoom",
    "CSCO": "Cisco",
    "SHOP": "Shopify",
    "ORCL": "Oracle",
    "IBM": "IBM",
    "DIS": "Disney",
    "NKE": "Nike",
    "PFE": "Pfizer",
    "ABT": "Abbott",
    "TMO": "Thermo Fisher Scientific",
    "ACN": "Accenture",
    "AVGO": "Broadcom",
    "TXN": "Texas Instruments",
    "COST": "Costco",
    "DHR": "Danaher",
    "NEE": "NextEra Energy",
    "LIN": "Linde",
    "VZ": "Verizon",
    "CMCSA": "Comcast",
    "PEP": "PepsiCo",
    "T": "AT&T",
    "WFC": "Wells Fargo",
    "BAC": "Bank of America",
    "XOM": "Exxon Mobil",
    "CVX": "Chevron",
    "KO": "Coca-Cola",
    "PG": "Procter & Gamble",
    "MRK": "Merck",
    "ABBV": "AbbVie",
    "LLY": "Eli Lilly",
    "UNH": "UnitedHealth",
    "HD": "Home Depot",
    "MA": "Mastercard",
    "AMGN": "Amgen",
    "LOW": "Lowe's",
    "SPGI": "S&P Global",
    "INTU": "Intuit",
    "ISRG": "Intuitive Surgical",
    "GILD": "Gilead Sciences",
    "ADP": "Automatic Data Processing",
    "BKNG": "Booking Holdings",
    "MDT": "Medtronic",
    "CB": "Chubb",
    "CI": "Cigna",
    "SO": "Southern Company",
    "DUK": "Duke Energy",
    "AON": "Aon",
    "CL": "Colgate-Palmolive",
    "EL": "Estée Lauder",
    "FIS": "Fidelity National Information Services",
    "ICE": "Intercontinental Exchange",
    "ITW": "Illinois Tool Works",
    "J": "Jacobs Engineering",
    "KMB": "Kimberly-Clark",
    "MMM": "3M",
    "NOC": "Northrop Grumman",
    "PNC": "PNC Financial Services",
    "RTX": "Raytheon Technologies",
    "SYY": "Sysco",
    "TGT": "Target",
    "USB": "U.S. Bancorp",
    "ZTS": "Zoetis"
}

def _classify_impact(title: str, content: str) -> str:
    """Classify news impact based on keywords."""
    text = (title + " " + content).lower()
    
    high_impact_keywords = [
        "earnings", "revenue", "profit", "loss", "beat", "miss", "guidance",
        "merger", "acquisition", "buyout", "bankruptcy", "lawsuit", "settlement",
        "fda", "approval", "rejection", "clinical trial", "drug", "treatment",
        "ceo", "cfo", "resignation", "appointment", "leadership change"
    ]
    
    medium_impact_keywords = [
        "partnership", "collaboration", "contract", "deal", "agreement",
        "expansion", "growth", "investment", "funding", "raise",
        "product", "launch", "release", "update", "upgrade"
    ]
    
    if any(keyword in text for keyword in high_impact_keywords):
        return "high"
    elif any(keyword in text for keyword in medium_impact_keywords):
        return "medium"
    else:
        return "low"

def _classify_sentiment(title: str, content: str) -> str:
    """Classify news sentiment based on keywords."""
    text = (title + " " + content).lower()
    
    positive_keywords = [
        "beat", "exceed", "strong", "growth", "profit", "gain", "rise", "up",
        "positive", "optimistic", "bullish", "success", "win", "breakthrough",
        "record", "high", "surge", "rally", "boom", "thrive"
    ]
    
    negative_keywords = [
        "miss", "fall", "decline", "drop", "loss", "weak", "struggle", "down",
        "negative", "pessimistic", "bearish", "fail", "crisis", "crash",
        "low", "plunge", "slump", "recession", "bankruptcy", "layoff"
    ]
    
    positive_count = sum(1 for keyword in positive_keywords if keyword in text)
    negative_count = sum(1 for keyword in negative_keywords if keyword in text)
    
    if positive_count > negative_count:
        return "positive"
    elif negative_count > positive_count:
        return "negative"
    else:
        return "neutral"

def fetch_trending_stocks() -> List[str]:
    """Fetch trending stock tickers."""
    try:
        from live_trade_bench.fetchers.stock_fetcher import fetch_trending_stocks
        stocks = fetch_trending_stocks()
        return stocks[:10]  # Limit to top 10
    except Exception as e:
        # Fallback to popular stocks
        return ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "AMD", "NFLX", "CRM"]

def fetch_trending_markets() -> List[str]:
    """Fetch trending polymarket topics."""
    try:
        from live_trade_bench.fetchers.polymarket_fetcher import fetch_trending_markets
        markets = fetch_trending_markets()
        return markets[:5]  # Limit to top 5
    except Exception as e:
        # Fallback topics
        return [
            "US Presidential Election 2024",
            "Bitcoin Price",
            "Federal Reserve Interest Rates",
            "AI Development",
            "Climate Change"
        ]

def fetch_stock_news(ticker: str) -> List[Dict[str, Any]]:
    """Fetch news for a specific stock ticker."""
    try:
        news_fetcher = NewsFetcher()
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        company_name = TICKER_TO_COMPANY.get(ticker.upper(), ticker)
        query = f"{ticker} stock OR {ticker} earnings OR {ticker} news"
        raw_news = news_fetcher.fetch(query, start_date, end_date, max_pages=1)
        
        formatted_news = []
        for i, article in enumerate(raw_news):
            title = article.get("title", "Stock Market Update")
            content = article.get("snippet", "Market news update")
            formatted_news.append({
                "id": f"real_stock_{ticker}_{i}_{int(time.time())}",
                "title": title,
                "summary": content,
                "source": article.get("source", "Financial News"),
                "published_at": article.get("date", datetime.now().isoformat()),
                "impact": _classify_impact(title, content),
                "category": "stock",
                "market_type": "stock",
                "stock_symbol": ticker,
                "url": article.get("link", f"https://finance.yahoo.com/quote/{ticker}"),
            })
        return formatted_news
    except Exception as e:
        return []

def fetch_polymarket_news(topic: str) -> List[Dict[str, Any]]:
    """Fetch news for a specific polymarket topic."""
    try:
        news_fetcher = NewsFetcher()
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        query = f"{topic} prediction market OR {topic} polymarket"
        raw_news = news_fetcher.fetch(query, start_date, end_date, max_pages=1)
        
        formatted_news = []
        for i, article in enumerate(raw_news):
            title = article.get("title", "Market Prediction Update")
            content = article.get("snippet", "Prediction market news update")
            formatted_news.append({
                "id": f"real_polymarket_{topic.replace(' ', '_')}_{i}_{int(time.time())}",
                "title": title,
                "summary": content,
                "source": article.get("source", "Prediction Market News"),
                "published_at": article.get("date", datetime.now().isoformat()),
                "impact": _classify_impact(title, content),
                "category": "polymarket",
                "market_type": "polymarket",
                "topic": topic,
                "url": article.get("link", "https://polymarket.com"),
            })
        return formatted_news
    except Exception as e:
        return []

def update_news_data():
    """Update news data and save to JSON file."""
    try:
        # Fetch news data
        news_data = {"stock": [], "polymarket": []}
        
        # Get trending stocks and markets
        stocks = fetch_trending_stocks()
        topics = fetch_trending_markets()
        
        # Fetch stock news in parallel
        with ThreadPoolExecutor(max_workers=5) as executor:
            stock_futures = {
                executor.submit(fetch_stock_news, ticker): ticker 
                for ticker in stocks
            }
            
            for future in as_completed(stock_futures):
                ticker = stock_futures[future]
                try:
                    news_items = future.result()
                    news_data["stock"].extend(news_items)
                except Exception as e:
                    pass
        
        # Fetch polymarket news in parallel
        with ThreadPoolExecutor(max_workers=3) as executor:
            polymarket_futures = {
                executor.submit(fetch_polymarket_news, topic): topic 
                for topic in topics
            }
            
            for future in as_completed(polymarket_futures):
                topic = polymarket_futures[future]
                try:
                    news_items = future.result()
                    news_data["polymarket"].extend(news_items)
                except Exception as e:
                    pass
        
        # Save to JSON file
        with open("news_data.json", "w") as f:
            json.dump(news_data, f, indent=2)
            
    except Exception:
        import traceback
        traceback.print_exc()

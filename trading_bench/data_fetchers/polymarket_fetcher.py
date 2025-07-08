"""
Polymarket data fetcher for trading bench.

This module provides functions to fetch prediction market data from Polymarket
using their API endpoints.
"""

import time
import random

import requests


def fetch_polymarket_markets(category: str = None, limit: int = 50) -> list:
    """
    Fetches available markets from Polymarket.
    Args:
        category: Market category filter (e.g., 'politics', 'sports', 'crypto').
        limit: Maximum number of markets to return.
    Returns:
        list: List of available markets with basic information.
    """
    # Random delay before each request to avoid rate limiting
    time.sleep(random.uniform(1, 3))
    
    try:
        # Polymarket API endpoint for markets
        url = "https://clob.polymarket.com/markets"
        
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/101.0.4951.54 Safari/537.36"
            ),
            "Accept": "application/json"
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        markets_data = response.json()
        
        # Filter by category if specified
        if category:
            markets_data = [
                market for market in markets_data 
                if category.lower() in market.get('category', '').lower()
            ]
        
        # Limit results
        markets_data = markets_data[:limit]
        
        # Extract relevant information
        markets = []
        for market in markets_data:
            markets.append({
                'id': market.get('id'),
                'title': market.get('title'),
                'category': market.get('category'),
                'description': market.get('description'),
                'end_date': market.get('endDate'),
                'status': market.get('status'),
                'total_volume': market.get('totalVolume'),
                'total_liquidity': market.get('totalLiquidity')
            })
        
        return markets
        
    except Exception as e:
        raise RuntimeError(f'Failed to fetch Polymarket markets: {e}')


def fetch_polymarket_market_details(market_id: str) -> dict:
    """
    Fetches detailed information for a specific Polymarket.
    Args:
        market_id: The unique identifier for the market.
    Returns:
        dict: Detailed market information including outcomes and current prices.
    """
    # Random delay before each request to avoid rate limiting
    time.sleep(random.uniform(1, 3))
    
    try:
        # Polymarket API endpoint for specific market
        url = f"https://clob.polymarket.com/markets/{market_id}"
        
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/101.0.4951.54 Safari/537.36"
            ),
            "Accept": "application/json"
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        market_data = response.json()
        
        # Extract outcomes and their current prices
        outcomes = []
        for outcome in market_data.get('outcomes', []):
            outcomes.append({
                'id': outcome.get('id'),
                'name': outcome.get('name'),
                'current_price': outcome.get('currentPrice'),
                'volume_24h': outcome.get('volume24h'),
                'liquidity': outcome.get('liquidity'),
                'probability': outcome.get('probability')
            })
        
        return {
            'id': market_data.get('id'),
            'title': market_data.get('title'),
            'description': market_data.get('description'),
            'category': market_data.get('category'),
            'status': market_data.get('status'),
            'end_date': market_data.get('endDate'),
            'total_volume': market_data.get('totalVolume'),
            'total_liquidity': market_data.get('totalLiquidity'),
            'outcomes': outcomes
        }
        
    except Exception as e:
        raise RuntimeError(f'Failed to fetch Polymarket market details: {e}')


def fetch_polymarket_orderbook(market_id: str, outcome_id: str = None) -> dict:
    """
    Fetches order book data for a specific market and outcome.
    Args:
        market_id: The unique identifier for the market.
        outcome_id: The specific outcome ID (optional).
    Returns:
        dict: Order book with bids and asks.
    """
    # Random delay before each request to avoid rate limiting
    time.sleep(random.uniform(1, 3))
    
    try:
        # Polymarket API endpoint for order book
        url = f"https://clob.polymarket.com/markets/{market_id}/orderbook"
        if outcome_id:
            url += f"?outcome={outcome_id}"
        
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/101.0.4951.54 Safari/537.36"
            ),
            "Accept": "application/json"
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        orderbook_data = response.json()
        
        return {
            'market_id': market_id,
            'outcome_id': outcome_id,
            'bids': orderbook_data.get('bids', []),
            'asks': orderbook_data.get('asks', []),
            'timestamp': orderbook_data.get('timestamp')
        }
        
    except Exception as e:
        raise RuntimeError(f'Failed to fetch Polymarket orderbook: {e}')


def fetch_polymarket_trades(market_id: str, limit: int = 100) -> list:
    """
    Fetches recent trades for a specific market.
    Args:
        market_id: The unique identifier for the market.
        limit: Maximum number of trades to return.
    Returns:
        list: List of recent trades with price and volume information.
    """
    # Random delay before each request to avoid rate limiting
    time.sleep(random.uniform(1, 3))
    
    try:
        # Polymarket API endpoint for trades
        url = f"https://clob.polymarket.com/markets/{market_id}/trades?limit={limit}"
        
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/101.0.4951.54 Safari/537.36"
            ),
            "Accept": "application/json"
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        trades_data = response.json()
        
        # Extract relevant trade information
        trades = []
        for trade in trades_data:
            trades.append({
                'id': trade.get('id'),
                'outcome_id': trade.get('outcomeId'),
                'price': trade.get('price'),
                'size': trade.get('size'),
                'side': trade.get('side'),  # 'buy' or 'sell'
                'timestamp': trade.get('timestamp'),
                'maker': trade.get('maker'),
                'taker': trade.get('taker')
            })
        
        return trades
        
    except Exception as e:
        raise RuntimeError(f'Failed to fetch Polymarket trades: {e}')


def fetch_polymarket_market_stats(market_id: str) -> dict:
    """
    Fetches market statistics and analytics.
    Args:
        market_id: The unique identifier for the market.
    Returns:
        dict: Market statistics including volume, liquidity, and price movements.
    """
    # Random delay before each request to avoid rate limiting
    time.sleep(random.uniform(1, 3))
    
    try:
        # Get market details first
        market_details = fetch_polymarket_market_details(market_id)
        
        # Get recent trades for volume analysis
        recent_trades = fetch_polymarket_trades(market_id, limit=100)
        
        # Calculate basic statistics
        total_volume_24h = sum(trade['size'] for trade in recent_trades)
        avg_price = sum(trade['price'] * trade['size'] for trade in recent_trades) / sum(trade['size'] for trade in recent_trades) if recent_trades else 0
        
        # Price movement analysis
        if len(recent_trades) >= 2:
            price_change = recent_trades[0]['price'] - recent_trades[-1]['price']
            price_change_pct = (price_change / recent_trades[-1]['price']) * 100 if recent_trades[-1]['price'] > 0 else 0
        else:
            price_change = 0
            price_change_pct = 0
        
        return {
            'market_id': market_id,
            'title': market_details.get('title'),
            'total_volume_24h': total_volume_24h,
            'average_price': avg_price,
            'price_change': price_change,
            'price_change_percent': price_change_pct,
            'total_trades_24h': len(recent_trades),
            'outcomes_count': len(market_details.get('outcomes', [])),
            'market_status': market_details.get('status'),
            'total_liquidity': market_details.get('totalLiquidity')
        }
        
    except Exception as e:
        raise RuntimeError(f'Failed to fetch Polymarket market stats: {e}')


def search_polymarket_markets(query: str, category: str = None) -> list:
    """
    Searches for markets based on a query string.
    Args:
        query: Search query string.
        category: Optional category filter.
    Returns:
        list: List of markets matching the search criteria.
    """
    # Random delay before each request to avoid rate limiting
    time.sleep(random.uniform(1, 3))
    
    try:
        # Get all markets first
        all_markets = fetch_polymarket_markets(category=category, limit=1000)
        
        # Filter by query
        query_lower = query.lower()
        matching_markets = []
        
        for market in all_markets:
            title = market.get('title', '').lower()
            description = market.get('description', '').lower()
            category_name = market.get('category', '').lower()
            
            if (query_lower in title or 
                query_lower in description or 
                query_lower in category_name):
                matching_markets.append(market)
        
        return matching_markets
        
    except Exception as e:
        raise RuntimeError(f'Failed to search Polymarket markets: {e}')


def fetch_polymarket_trending_markets(limit: int = 10) -> list:
    """
    Fetches trending markets based on volume and activity.
    Args:
        limit: Maximum number of trending markets to return.
    Returns:
        list: List of trending markets sorted by activity.
    """
    # Random delay before each request to avoid rate limiting
    time.sleep(random.uniform(1, 3))
    
    try:
        # Get all markets
        all_markets = fetch_polymarket_markets(limit=1000)
        
        # Sort by total volume (proxy for trending)
        trending_markets = sorted(
            all_markets,
            key=lambda x: x.get('total_volume', 0),
            reverse=True
        )
        
        return trending_markets[:limit]
        
    except Exception as e:
        raise RuntimeError(f'Failed to fetch trending Polymarket markets: {e}') 
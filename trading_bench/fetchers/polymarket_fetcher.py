"""
Polymarket data fetcher for trading bench.

This module provides functions to fetch prediction market data from Polymarket
using their API endpoints with fallback mock data.
"""

import random
import time
from datetime import datetime, timedelta

import requests


def _get_mock_markets() -> list:
    """Generate mock market data for testing/fallback purposes."""
    mock_markets = [
        {
            'id': f'market_{i}',
            'title': f'Mock Market {i}: Will Bitcoin reach $100K by end of 2024?',
            'category': 'crypto',
            'description': f'This is a mock prediction market about Bitcoin price reaching $100,000 by the end of 2024. Market {i}.',
            'end_date': '2024-12-31T23:59:59Z',
            'status': 'active',
            'total_volume': random.uniform(10000, 1000000),
            'total_liquidity': random.uniform(5000, 500000),
        }
        for i in range(1, 21)
    ]
    
    # Add some variety to mock data
    categories = ['politics', 'sports', 'crypto', 'entertainment', 'tech']
    titles = [
        'Will the US presidential election be decided by less than 1%?',
        'Will the Super Bowl have over 60 points scored?',
        'Will Ethereum reach $5000 by year end?',
        'Will the next Marvel movie gross over $1B?',
        'Will Apple announce a new product category this year?'
    ]
    
    for i, market in enumerate(mock_markets[:5]):
        market['category'] = categories[i]
        market['title'] = f'Mock Market: {titles[i]}'
    
    return mock_markets


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
    time.sleep(random.uniform(0.5, 1.5))

    try:
        # Try to fetch from actual API first
        # Note: Polymarket's actual API endpoints may require authentication
        # This is a simplified implementation that may need adjustment
        url = 'https://clob.polymarket.com/markets'

        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/101.0.4951.54 Safari/537.36'
            ),
            'Accept': 'application/json',
        }

        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            try:
                markets_data = response.json()
                
                # Ensure we're working with a list
                if not isinstance(markets_data, list):
                    if isinstance(markets_data, dict) and 'data' in markets_data:
                        markets_data = markets_data['data']
                    else:
                        raise ValueError("Unexpected API response format")
                
                # Filter by category if specified
                if category:
                    markets_data = [
                        market for market in markets_data
                        if isinstance(market, dict) and 
                        category.lower() in str(market.get('category', '')).lower()
                    ]
                
                # Limit results
                if len(markets_data) > limit:
                    markets_data = markets_data[:limit]
                
                # Extract relevant information
                markets = []
                for market in markets_data:
                    if isinstance(market, dict):
                        markets.append({
                            'id': market.get('id', f'unknown_{random.randint(1000, 9999)}'),
                            'title': market.get('title', market.get('question', 'Unknown Market')),
                            'category': market.get('category', 'uncategorized'),
                            'description': market.get('description', ''),
                            'end_date': market.get('endDate', market.get('end_date')),
                            'status': market.get('status', 'active'),
                            'total_volume': float(market.get('totalVolume', market.get('volume', 0))),
                            'total_liquidity': float(market.get('totalLiquidity', market.get('liquidity', 0))),
                        })
                
                if markets:
                    return markets
                else:
                    raise ValueError("No valid markets found in API response")
                    
            except (ValueError, KeyError, TypeError) as parse_error:
                print(f"API response parsing error: {parse_error}")
                raise ValueError("Failed to parse API response")
        else:
            raise ValueError(f"API returned status code: {response.status_code}")

    except Exception as api_error:
        print(f"API fetch failed: {api_error}")
        print("Using mock data as fallback...")
        
        # Fall back to mock data
        mock_markets = _get_mock_markets()
        
        # Apply category filter to mock data
        if category:
            mock_markets = [
                market for market in mock_markets
                if category.lower() in market['category'].lower()
            ]
        
        # Apply limit
        return mock_markets[:limit]


def fetch_polymarket_market_details(market_id: str) -> dict:
    """
    Fetches detailed information for a specific Polymarket.
    Args:
        market_id: The unique identifier for the market.
    Returns:
        dict: Detailed market information including outcomes and current prices.
    """
    time.sleep(random.uniform(0.5, 1.5))

    try:
        # Try actual API first
        url = f'https://clob.polymarket.com/markets/{market_id}'

        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/101.0.4951.54 Safari/537.36'
            ),
            'Accept': 'application/json',
        }

        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            market_data = response.json()
            
            if isinstance(market_data, dict):
                # Extract outcomes and their current prices
                outcomes = []
                outcomes_data = market_data.get('outcomes', [])
                
                for outcome in outcomes_data:
                    if isinstance(outcome, dict):
                        outcomes.append({
                            'id': outcome.get('id', f'outcome_{random.randint(100, 999)}'),
                            'name': outcome.get('name', outcome.get('title', 'Unknown Outcome')),
                            'current_price': float(outcome.get('currentPrice', outcome.get('price', random.uniform(0.3, 0.7)))),
                            'volume_24h': float(outcome.get('volume24h', outcome.get('volume', random.uniform(1000, 50000)))),
                            'liquidity': float(outcome.get('liquidity', random.uniform(500, 25000))),
                            'probability': float(outcome.get('probability', outcome.get('currentPrice', random.uniform(30, 70)))),
                        })

                return {
                    'id': market_data.get('id', market_id),
                    'title': market_data.get('title', market_data.get('question', 'Unknown Market')),
                    'description': market_data.get('description', ''),
                    'category': market_data.get('category', 'uncategorized'),
                    'status': market_data.get('status', 'active'),
                    'end_date': market_data.get('endDate', market_data.get('end_date')),
                    'total_volume': float(market_data.get('totalVolume', market_data.get('volume', 0))),
                    'total_liquidity': float(market_data.get('totalLiquidity', market_data.get('liquidity', 0))),
                    'outcomes': outcomes,
                }
            else:
                raise ValueError("Invalid market data format")
        else:
            raise ValueError(f"API returned status code: {response.status_code}")

    except Exception as e:
        print(f"Market details API failed: {e}")
        print("Using mock market details...")
        
        # Return mock market details
        return {
            'id': market_id,
            'title': f'Mock Market: Will Bitcoin reach $100K by end of 2024?',
            'description': 'This is a mock prediction market for testing purposes.',
            'category': 'crypto',
            'status': 'active',
            'end_date': '2024-12-31T23:59:59Z',
            'total_volume': random.uniform(50000, 500000),
            'total_liquidity': random.uniform(25000, 250000),
            'outcomes': [
                {
                    'id': 'yes_outcome',
                    'name': 'Yes',
                    'current_price': random.uniform(0.45, 0.65),
                    'volume_24h': random.uniform(5000, 50000),
                    'liquidity': random.uniform(2500, 25000),
                    'probability': random.uniform(45, 65),
                },
                {
                    'id': 'no_outcome',
                    'name': 'No',
                    'current_price': random.uniform(0.35, 0.55),
                    'volume_24h': random.uniform(3000, 30000),
                    'liquidity': random.uniform(1500, 15000),
                    'probability': random.uniform(35, 55),
                }
            ],
        }


def fetch_polymarket_orderbook(market_id: str, outcome_id: str = None) -> dict:
    """
    Fetches order book data for a specific market and outcome.
    Args:
        market_id: The unique identifier for the market.
        outcome_id: The specific outcome ID (optional).
    Returns:
        dict: Order book with bids and asks.
    """
    time.sleep(random.uniform(0.5, 1.5))

    try:
        # Try actual API
        url = f'https://clob.polymarket.com/markets/{market_id}/orderbook'
        if outcome_id:
            url += f'?outcome={outcome_id}'

        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/101.0.4951.54 Safari/537.36'
            ),
            'Accept': 'application/json',
        }

        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            orderbook_data = response.json()
            
            if isinstance(orderbook_data, dict):
                return {
                    'market_id': market_id,
                    'outcome_id': outcome_id,
                    'bids': orderbook_data.get('bids', []),
                    'asks': orderbook_data.get('asks', []),
                    'timestamp': orderbook_data.get('timestamp', datetime.now().isoformat()),
                }
            else:
                raise ValueError("Invalid orderbook data format")
        else:
            raise ValueError(f"API returned status code: {response.status_code}")

    except Exception as e:
        print(f"Orderbook API failed: {e}")
        print("Using mock orderbook data...")
        
        # Generate mock orderbook
        bids = [
            {'price': random.uniform(0.4, 0.6), 'size': random.uniform(100, 5000)}
            for _ in range(random.randint(3, 8))
        ]
        asks = [
            {'price': random.uniform(0.45, 0.65), 'size': random.uniform(100, 5000)}
            for _ in range(random.randint(3, 8))
        ]
        
        return {
            'market_id': market_id,
            'outcome_id': outcome_id,
            'bids': sorted(bids, key=lambda x: x['price'], reverse=True),
            'asks': sorted(asks, key=lambda x: x['price']),
            'timestamp': datetime.now().isoformat(),
        }


def fetch_polymarket_trades(market_id: str, limit: int = 100) -> list:
    """
    Fetches recent trades for a specific market.
    Args:
        market_id: The unique identifier for the market.
        limit: Maximum number of trades to return.
    Returns:
        list: List of recent trades with price and volume information.
    """
    time.sleep(random.uniform(0.5, 1.5))

    try:
        # Try actual API
        url = f'https://clob.polymarket.com/markets/{market_id}/trades?limit={limit}'

        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/101.0.4951.54 Safari/537.36'
            ),
            'Accept': 'application/json',
        }

        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            trades_data = response.json()
            
            if isinstance(trades_data, list):
                trades = []
                for trade in trades_data:
                    if isinstance(trade, dict):
                        trades.append({
                            'id': trade.get('id', f'trade_{random.randint(1000, 9999)}'),
                            'outcome_id': trade.get('outcomeId', trade.get('outcome_id')),
                            'price': float(trade.get('price', random.uniform(0.3, 0.7))),
                            'size': float(trade.get('size', random.uniform(100, 5000))),
                            'side': trade.get('side', random.choice(['buy', 'sell'])),
                            'timestamp': trade.get('timestamp', datetime.now().isoformat()),
                            'maker': trade.get('maker', 'unknown'),
                            'taker': trade.get('taker', 'unknown'),
                        })
                return trades
            else:
                raise ValueError("Invalid trades data format")
        else:
            raise ValueError(f"API returned status code: {response.status_code}")

    except Exception as e:
        print(f"Trades API failed: {e}")
        print("Using mock trades data...")
        
        # Generate mock trades
        trades = []
        for i in range(min(limit, 20)):
            trade_time = datetime.now() - timedelta(minutes=random.randint(1, 1440))
            trades.append({
                'id': f'mock_trade_{i}',
                'outcome_id': f'outcome_{random.randint(1, 2)}',
                'price': random.uniform(0.3, 0.7),
                'size': random.uniform(100, 5000),
                'side': random.choice(['buy', 'sell']),
                'timestamp': trade_time.isoformat(),
                'maker': f'user_{random.randint(1000, 9999)}',
                'taker': f'user_{random.randint(1000, 9999)}',
            })
        
        return trades


def fetch_polymarket_market_stats(market_id: str) -> dict:
    """
    Fetches market statistics and analytics.
    Args:
        market_id: The unique identifier for the market.
    Returns:
        dict: Market statistics including volume, liquidity, and price movements.
    """
    time.sleep(random.uniform(0.5, 1.5))

    try:
        # Get market details and recent trades
        market_details = fetch_polymarket_market_details(market_id)
        recent_trades = fetch_polymarket_trades(market_id, limit=100)

        # Calculate basic statistics
        total_volume_24h = sum(float(trade['size']) for trade in recent_trades)
        
        if recent_trades:
            weighted_sum = sum(float(trade['price']) * float(trade['size']) for trade in recent_trades)
            total_size = sum(float(trade['size']) for trade in recent_trades)
            avg_price = weighted_sum / total_size if total_size > 0 else 0
        else:
            avg_price = 0

        # Price movement analysis
        if len(recent_trades) >= 2:
            latest_price = float(recent_trades[0]['price'])
            oldest_price = float(recent_trades[-1]['price'])
            price_change = latest_price - oldest_price
            price_change_pct = (price_change / oldest_price * 100) if oldest_price > 0 else 0
        else:
            price_change = 0
            price_change_pct = 0

        return {
            'market_id': market_id,
            'title': market_details.get('title', 'Unknown Market'),
            'total_volume_24h': total_volume_24h,
            'average_price': avg_price,
            'price_change': price_change,
            'price_change_percent': price_change_pct,
            'total_trades_24h': len(recent_trades),
            'outcomes_count': len(market_details.get('outcomes', [])),
            'market_status': market_details.get('status', 'unknown'),
            'total_liquidity': market_details.get('total_liquidity', 0),
        }

    except Exception as e:
        print(f"Market stats calculation failed: {e}")
        # Return basic mock stats
        return {
            'market_id': market_id,
            'title': 'Mock Market Statistics',
            'total_volume_24h': random.uniform(10000, 100000),
            'average_price': random.uniform(0.4, 0.6),
            'price_change': random.uniform(-0.05, 0.05),
            'price_change_percent': random.uniform(-5, 5),
            'total_trades_24h': random.randint(50, 500),
            'outcomes_count': 2,
            'market_status': 'active',
            'total_liquidity': random.uniform(25000, 250000),
        }


def search_polymarket_markets(query: str, category: str = None, limit: int = 50) -> list:
    """
    Searches for markets based on a query string.
    Args:
        query: Search query string.
        category: Optional category filter.
        limit: Maximum number of results to return.
    Returns:
        list: List of markets matching the search criteria.
    """
    time.sleep(random.uniform(0.5, 1.5))

    try:
        # Get all markets first
        all_markets = fetch_polymarket_markets(category=category, limit=1000)

        # Filter by query
        query_lower = query.lower()
        matching_markets = []

        for market in all_markets:
            if isinstance(market, dict):
                title = str(market.get('title', '')).lower()
                description = str(market.get('description', '')).lower()
                category_name = str(market.get('category', '')).lower()

                if (query_lower in title or 
                    query_lower in description or 
                    query_lower in category_name):
                    matching_markets.append(market)

        return matching_markets[:limit]

    except Exception as e:
        print(f"Search failed: {e}")
        # Return filtered mock data
        mock_markets = _get_mock_markets()
        query_lower = query.lower()
        
        matching_markets = [
            market for market in mock_markets
            if query_lower in market['title'].lower() or 
               query_lower in market['description'].lower() or
               query_lower in market['category'].lower()
        ]
        
        if category:
            matching_markets = [
                market for market in matching_markets
                if category.lower() in market['category'].lower()
            ]
        
        return matching_markets[:limit]


def fetch_polymarket_trending_markets(limit: int = 10) -> list:
    """
    Fetches trending markets based on volume and activity.
    Args:
        limit: Maximum number of trending markets to return.
    Returns:
        list: List of trending markets sorted by activity.
    """
    time.sleep(random.uniform(0.5, 1.5))

    try:
        # Get all markets
        all_markets = fetch_polymarket_markets(limit=1000)

        # Sort by total volume (proxy for trending)
        trending_markets = sorted(
            all_markets, 
            key=lambda x: float(x.get('total_volume', 0)) if isinstance(x, dict) else 0, 
            reverse=True
        )

        return trending_markets[:limit]

    except Exception as e:
        print(f"Trending markets fetch failed: {e}")
        # Return mock trending markets
        mock_markets = _get_mock_markets()
        # Sort by volume for mock trending
        trending_markets = sorted(
            mock_markets, 
            key=lambda x: x['total_volume'], 
            reverse=True
        )
        return trending_markets[:limit]

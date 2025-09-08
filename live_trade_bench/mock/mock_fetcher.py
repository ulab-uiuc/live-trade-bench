"""
Mock Fetchers - Generate fake but realistic data for testing
"""

import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from live_trade_bench.fetchers.base_fetcher import BaseFetcher


class MockBaseFetcher(BaseFetcher):
    """Mock base fetcher that eliminates network delays and external dependencies"""

    def __init__(self, min_delay: float = 0.01, max_delay: float = 0.05):
        # Minimal delays for mock - no network calls
        super().__init__(min_delay, max_delay)

    def make_request(
        self, url: str, headers: Optional[Dict[str, str]] = None, **kwargs: Any
    ) -> Any:
        # Mock request - return empty response since we generate data directly
        class MockResponse:
            def __init__(self):
                self.status_code = 200
                self.ok = True

        return MockResponse()


class MockNewsFetcher(MockBaseFetcher):
    """Mock news fetcher generating fake news data"""

    def __init__(self, min_delay: float = 0.01, max_delay: float = 0.05):
        super().__init__(min_delay, max_delay)

    def fetch(
        self, query: str, start_date: str, end_date: str, max_pages: int = 10
    ) -> List[Dict[str, Any]]:
        """Generate mock news data matching real NewsFetcher format"""

        # Sample news templates
        news_templates = [
            {
                "title_template": "{query} Stock Surges on Strong Earnings Report",
                "snippet_template": "Shares of {query} jumped after reporting better-than-expected quarterly results...",
                "source": "MarketWatch",
            },
            {
                "title_template": "Analysts Upgrade {query} Price Target",
                "snippet_template": "Wall Street analysts have raised their price targets for {query} following...",
                "source": "Yahoo Finance",
            },
            {
                "title_template": "{query} Announces New Partnership Deal",
                "snippet_template": "The company unveiled a strategic partnership that could boost revenue...",
                "source": "Reuters",
            },
            {
                "title_template": "Market Volatility Impacts {query} Trading",
                "snippet_template": "Recent market conditions have affected trading volumes for {query}...",
                "source": "Bloomberg",
            },
            {
                "title_template": "{query} Reports Mixed Quarter Results",
                "snippet_template": "The latest quarterly report from {query} showed mixed performance...",
                "source": "CNBC",
            },
        ]

        news_results = []
        num_articles = min(max_pages * 8, 50)  # Realistic number of results

        # Generate date range
        start_dt = datetime.strptime(
            start_date.split()[0] if " " in start_date else start_date,
            "%Y-%m-%d" if "-" in start_date else "%m/%d/%Y",
        )
        end_dt = datetime.strptime(
            end_date.split()[0] if " " in end_date else end_date,
            "%Y-%m-%d" if "-" in end_date else "%m/%d/%Y",
        )

        for i in range(num_articles):
            template = random.choice(news_templates)

            # Generate random date in range
            time_diff = end_dt - start_dt
            random_days = random.randint(0, max(1, time_diff.days))
            article_date = start_dt + timedelta(days=random_days)

            # Format varies - match real fetcher behavior
            date_formats = [
                f"{random.randint(1, 30)} hours ago",
                f"{random.randint(1, 7)} days ago",
                article_date.strftime("%b %d, %Y"),
                article_date.strftime("%m/%d/%Y"),
            ]

            article = {
                "link": f"https://example-news-site.com/article/{i+1}",
                "title": template["title_template"].format(query=query),
                "snippet": template["snippet_template"].format(query=query),
                "date": random.choice(date_formats),
                "source": template["source"],
            }

            news_results.append(article)

        return news_results


class MockRedditFetcher(MockBaseFetcher):
    """Mock Reddit fetcher generating fake social media data"""

    def __init__(self, min_delay: float = 0.01, max_delay: float = 0.05):
        super().__init__(min_delay, max_delay)

    def fetch(
        self,
        category: str,
        query: Optional[str] = None,
        max_limit: int = 50,
        time_filter: str = "day",
    ) -> List[Dict[str, Any]]:
        """Generate mock Reddit posts matching real RedditFetcher format"""

        # Mock subreddits based on category
        category_subreddits = {
            "company_news": [
                "investing",
                "stocks",
                "SecurityAnalysis",
                "ValueInvesting",
            ],
            "options": ["options", "thetagang", "wallstreetbets"],
            "market": [
                "StockMarket",
                "investing",
                "wallstreetbets",
                "SecurityAnalysis",
            ],
            "tech": ["technology", "stocks", "investing"],
        }

        subreddits = category_subreddits.get(category, ["investing"])

        # Post templates
        post_templates = [
            {
                "title_template": "DD: Why {query} is undervalued",
                "content_template": "After extensive research, I believe {query} presents a compelling investment opportunity...",
            },
            {
                "title_template": "{query} earnings discussion",
                "content_template": "What are your thoughts on {query}'s latest earnings? The numbers look...",
            },
            {
                "title_template": "Is {query} a good buy right now?",
                "content_template": "Thinking about adding {query} to my portfolio. What do you think about...",
            },
            {
                "title_template": "{query} technical analysis",
                "content_template": "Looking at the charts for {query}, I'm seeing some interesting patterns...",
            },
            {
                "title_template": "News: {query} announces new developments",
                "content_template": "Just saw this news about {query}. Could have significant impact on stock price...",
            },
        ]

        all_posts = []
        num_posts = min(max_limit, 100)

        for i in range(num_posts):
            template = random.choice(post_templates)
            subreddit = random.choice(subreddits)

            # Generate realistic engagement metrics
            upvotes = random.randint(5, 2000)
            comments = random.randint(2, 150)
            score = upvotes + random.randint(-50, 100)

            # Generate date within recent timeframe
            days_ago = random.randint(0, 7)
            post_date = datetime.now() - timedelta(days=days_ago)
            created_utc = post_date.timestamp()

            post_data = {
                "title": template["title_template"].format(query=query or "AAPL"),
                "content": template["content_template"].format(query=query or "AAPL"),
                "url": f"https://www.reddit.com/r/{subreddit}/comments/{i+1}/",
                "upvotes": upvotes,
                "posted_date": post_date.strftime("%Y-%m-%d"),
                "subreddit": subreddit,
                "score": score,
                "num_comments": comments,
                "author": f"user{random.randint(1, 10000)}",
                "created_utc": created_utc,
                "id": f"mock_post_{i+1}",
            }

            all_posts.append(post_data)

        return all_posts[:max_limit]

    def fetch_top_from_category(
        self,
        category: str,
        date: str,
        max_limit: int,
        query: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        return self.fetch(category=category, query=query, max_limit=max_limit)

    def fetch_posts_by_ticker(
        self, ticker: str, date: str, max_limit: int = 50
    ) -> List[Dict[str, Any]]:
        return self.fetch(category="company_news", query=ticker, max_limit=max_limit)

    def fetch_sentiment_data(
        self, category: str, date: str, max_limit: int = 100
    ) -> List[Dict[str, Any]]:
        posts = self.fetch(category=category, max_limit=max_limit)
        for post in posts:
            post["text_for_sentiment"] = f"{post['title']} {post['content']}"
            post["engagement_score"] = post["upvotes"] + (post["num_comments"] * 2)
        return posts

    def get_available_categories(self) -> List[str]:
        return ["company_news", "options", "market", "tech"]

    def get_available_dates(self, category: str) -> List[str]:
        return [datetime.now().strftime("%Y-%m-%d")]

    def get_statistics(self, category: str, date: str) -> Dict[str, Any]:
        posts = self.fetch(category=category, max_limit=100)
        if not posts:
            return {
                "total_posts": 0,
                "total_upvotes": 0,
                "total_comments": 0,
                "avg_upvotes": 0,
                "avg_comments": 0,
                "top_post": None,
                "subreddits": [],
            }

        total_upvotes = sum(post["upvotes"] for post in posts)
        total_comments = sum(post["num_comments"] for post in posts)
        subreddits = list(set(post["subreddit"] for post in posts))
        top_post = max(posts, key=lambda x: x["upvotes"])

        return {
            "total_posts": len(posts),
            "total_upvotes": total_upvotes,
            "total_comments": total_comments,
            "avg_upvotes": total_upvotes / len(posts),
            "avg_comments": total_comments / len(posts),
            "top_post": {
                "title": top_post["title"],
                "upvotes": top_post["upvotes"],
                "subreddit": top_post["subreddit"],
            },
            "subreddits": subreddits,
        }


class MockStockFetcher(MockBaseFetcher):
    """Mock stock fetcher generating fake market data"""

    def __init__(self, min_delay: float = 0.01, max_delay: float = 0.05):
        super().__init__(min_delay, max_delay)

        # Base prices for consistent mock data
        self.base_prices = {
            "AAPL": 180.0,
            "MSFT": 420.0,
            "NVDA": 170.0,
            "JPM": 160.0,
            "V": 260.0,
            "JNJ": 170.0,
            "UNH": 520.0,
            "PG": 160.0,
            "KO": 60.0,
            "XOM": 110.0,
            "CAT": 280.0,
            "WMT": 160.0,
            "META": 480.0,
            "TSLA": 240.0,
            "AMZN": 150.0,
        }

    def fetch(self, mode: str, **kwargs: Any) -> Union[List[str], Optional[float]]:
        if mode == "trending_stocks":
            return self.get_trending_stocks(limit=int(kwargs.get("limit", 15)))
        elif mode == "stock_price":
            ticker = kwargs.get("ticker")
            if ticker is None:
                raise ValueError("ticker is required for stock_price")
            date = kwargs.get("date")
            return self.get_price(str(ticker), date=date)
        else:
            raise ValueError(f"Unknown fetch mode: {mode}")

    def get_trending_stocks(self, limit: int = 15) -> List[str]:
        """Return same stock list as real fetcher"""
        diversified_tickers = [
            "AAPL",
            "MSFT",
            "NVDA",
            "JPM",
            "V",
            "JNJ",
            "UNH",
            "PG",
            "KO",
            "XOM",
            "CAT",
            "WMT",
            "META",
            "TSLA",
            "AMZN",
        ]
        return diversified_tickers[:limit]

    def get_price(self, ticker: str, date: Optional[str] = None) -> Optional[float]:
        """Generate realistic but fake stock prices"""
        base_price = self.base_prices.get(ticker, 100.0)

        # Add some randomness to make it realistic
        random_factor = random.uniform(0.95, 1.05)  # �5% variation
        price = base_price * random_factor

        # If date is provided, add date-based variation
        if date:
            try:
                date_obj = datetime.strptime(date, "%Y-%m-%d")
                # Add small trend based on how far back the date is
                days_ago = (datetime.now() - date_obj).days
                trend_factor = 1.0 - (
                    days_ago * 0.001
                )  # Slight downward trend over time
                price *= max(0.8, trend_factor)  # Don't go too low
            except ValueError:
                pass

        return round(price, 2)

    def get_current_price(self, ticker: str) -> Optional[float]:
        return self.get_price(ticker)

    def fetch_stock_data(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
        interval: str = "1d",
    ) -> Dict[str, Any]:
        """Generate mock time series data"""
        # For mock, just return a simple structure
        # Real implementation would return pandas DataFrame
        base_price = self.base_prices.get(ticker, 100.0)

        return {
            "ticker": ticker,
            "start_date": start_date,
            "end_date": end_date,
            "interval": interval,
            "price": base_price * random.uniform(0.95, 1.05),
            "mock_data": True,
        }


class MockOptionFetcher(MockBaseFetcher):
    """Mock option fetcher generating fake options data"""

    def __init__(self, min_delay: float = 0.01, max_delay: float = 0.05):
        super().__init__(min_delay, max_delay)

    def fetch(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError(
            "MockOptionFetcher does not have a general fetch method. Please use specialized methods such as fetch_option_chain or fetch_option_data."
        )

    def fetch_option_chain(
        self, ticker: str, expiration_date: str | None = None
    ) -> Dict[str, Any]:
        """Generate mock options chain data"""

        # Mock underlying price
        base_prices = {"AAPL": 180.0, "MSFT": 420.0, "TSLA": 240.0}
        underlying_price = base_prices.get(ticker, 100.0) * random.uniform(0.98, 1.02)

        # Generate expiration dates
        available_exps = []
        for i in range(1, 8):  # Next 7 weeks
            exp_date = (datetime.now() + timedelta(weeks=i)).strftime("%Y-%m-%d")
            available_exps.append(exp_date)

        target_exp = expiration_date or available_exps[0]

        # Generate option strikes around current price
        strikes = []
        for i in range(-10, 11):  # 20 strikes total
            strike = round(underlying_price + (i * 5), 0)  # $5 intervals
            strikes.append(strike)

        # Generate calls
        calls = []
        for strike in strikes:
            moneyness = strike - underlying_price
            if moneyness < 0:  # ITM
                bid_price = abs(moneyness) + random.uniform(0.5, 2.0)
                ask_price = bid_price + random.uniform(0.05, 0.25)
            else:  # OTM
                bid_price = random.uniform(0.05, 5.0)
                ask_price = bid_price + random.uniform(0.05, 0.25)

            call = {
                "contractSymbol": f"{ticker}{target_exp.replace('-', '')[:6]}C{int(strike):08d}",
                "strike": strike,
                "lastPrice": round((bid_price + ask_price) / 2, 2),
                "bid": round(bid_price, 2),
                "ask": round(ask_price, 2),
                "volume": random.randint(0, 1000),
                "openInterest": random.randint(0, 5000),
                "impliedVolatility": round(random.uniform(0.15, 0.80), 4),
            }
            calls.append(call)

        # Generate puts (similar logic)
        puts = []
        for strike in strikes:
            moneyness = underlying_price - strike
            if moneyness < 0:  # ITM
                bid_price = abs(moneyness) + random.uniform(0.5, 2.0)
                ask_price = bid_price + random.uniform(0.05, 0.25)
            else:  # OTM
                bid_price = random.uniform(0.05, 5.0)
                ask_price = bid_price + random.uniform(0.05, 0.25)

            put = {
                "contractSymbol": f"{ticker}{target_exp.replace('-', '')[:6]}P{int(strike):08d}",
                "strike": strike,
                "lastPrice": round((bid_price + ask_price) / 2, 2),
                "bid": round(bid_price, 2),
                "ask": round(ask_price, 2),
                "volume": random.randint(0, 1000),
                "openInterest": random.randint(0, 5000),
                "impliedVolatility": round(random.uniform(0.15, 0.80), 4),
            }
            puts.append(put)

        result = {
            "ticker": ticker,
            "expiration": target_exp,
            "calls": calls,
            "puts": puts,
            "underlying_price": round(underlying_price, 2),
        }

        if not expiration_date:
            result["available_expirations"] = available_exps

        return result

    def fetch_option_data(
        self,
        ticker: str,
        expiration_date: str,
        option_type: str = "both",
        min_strike: float | None = None,
        max_strike: float | None = None,
    ) -> Dict[str, Any]:
        """Generate filtered mock option data"""
        chain_data = self.fetch_option_chain(ticker, expiration_date)

        result = {
            "ticker": ticker,
            "expiration": expiration_date,
            "underlying_price": chain_data["underlying_price"],
            "calls": [],
            "puts": [],
        }

        if option_type in ["calls", "both"]:
            calls = chain_data["calls"]
            if min_strike is not None:
                calls = [c for c in calls if c["strike"] >= min_strike]
            if max_strike is not None:
                calls = [c for c in calls if c["strike"] <= max_strike]
            result["calls"] = calls

        if option_type in ["puts", "both"]:
            puts = chain_data["puts"]
            if min_strike is not None:
                puts = [p for p in puts if p["strike"] >= min_strike]
            if max_strike is not None:
                puts = [p for p in puts if p["strike"] <= max_strike]
            result["puts"] = puts

        return result

    def fetch_option_expirations(self, ticker: str) -> List[str]:
        """Generate mock expiration dates"""
        expirations = []
        for i in range(1, 8):
            exp_date = (datetime.now() + timedelta(weeks=i)).strftime("%Y-%m-%d")
            expirations.append(exp_date)
        return expirations


# Export convenience functions matching real fetchers
def fetch_news_data(
    query: str, start_date: str, end_date: str, max_pages: int = 10
) -> List[Dict[str, Any]]:
    fetcher = MockNewsFetcher()
    return fetcher.fetch(query, start_date, end_date, max_pages)


def fetch_top_from_category(
    category: str,
    date: str,
    max_limit: int,
    query: Optional[str] = None,
) -> List[Dict[str, Any]]:
    fetcher = MockRedditFetcher()
    return fetcher.fetch_top_from_category(category, date, max_limit, query)


def fetch_reddit_posts_by_ticker(
    ticker: str, date: str, max_limit: int = 50
) -> List[Dict[str, Any]]:
    fetcher = MockRedditFetcher()
    return fetcher.fetch_posts_by_ticker(ticker, date, max_limit)


def fetch_reddit_sentiment_data(
    category: str, date: str, max_limit: int = 100
) -> List[Dict[str, Any]]:
    fetcher = MockRedditFetcher()
    return fetcher.fetch_sentiment_data(category, date, max_limit)


def fetch_trending_stocks(limit: int = 15) -> List[str]:
    fetcher = MockStockFetcher()
    return fetcher.get_trending_stocks(limit=limit)


def fetch_current_stock_price(ticker: str) -> Optional[float]:
    fetcher = MockStockFetcher()
    return fetcher.get_price(ticker)


def fetch_stock_price_on_date(ticker: str, date: str) -> Optional[float]:
    fetcher = MockStockFetcher()
    return fetcher.get_price(ticker, date=date)


def fetch_stock_price(ticker: str, date: Optional[str] = None) -> Optional[float]:
    fetcher = MockStockFetcher()
    return fetcher.get_price(ticker, date=date)


def fetch_polymarket_data(market_slugs: List[str]) -> Dict[str, Any]:
    """Generate mock polymarket data"""
    # This is a simplified mock. A more advanced version could simulate price changes.
    return {
        slug: {
            "yes_price": round(random.uniform(0.01, 0.99), 2),
            "no_price": round(random.uniform(0.01, 0.99), 2),
        }
        for slug in market_slugs
    }

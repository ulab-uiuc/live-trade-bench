"""Tests for data fetching functionality."""

from unittest.mock import Mock, patch

import pytest

from trading_bench.data_fetchers.news_fetcher import (
    fetch_news_data,
    is_rate_limited,
    make_request,
)
from trading_bench.data_fetchers.polymarket_fetcher import (
    fetch_polymarket_market_details,
    fetch_polymarket_market_stats,
    fetch_polymarket_markets,
    fetch_polymarket_trades,
    fetch_polymarket_trending_markets,
    search_polymarket_markets,
)
from trading_bench.data_fetchers.stock_fetcher import (
    _download_price_data,
    calculate_option_greeks,
    fetch_option_chain,
    fetch_option_data,
    fetch_option_expirations,
    fetch_option_historical_data,
    fetch_stock_data,
)


def test_is_rate_limited():
    """Test rate limiting detection."""
    # Test rate limited response
    mock_response = Mock()
    mock_response.status_code = 429
    assert is_rate_limited(mock_response) is True

    # Test normal response
    mock_response.status_code = 200
    assert is_rate_limited(mock_response) is False


@patch('trading_bench.fetchers.news_fetcher.requests.get')
def test_make_request(mock_get):
    """Test request making with retry logic."""
    # Mock successful response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    url = 'https://example.com'
    headers = {'User-Agent': 'test'}

    response = make_request(url, headers)

    assert response.status_code == 200
    mock_get.assert_called_once_with(url, headers=headers)


@patch('trading_bench.fetchers.news_fetcher.make_request')
def test_fetch_news_data_basic(mock_make_request):
    """Test basic news data fetching functionality."""
    # Mock HTML response
    mock_response = Mock()
    mock_response.content = """
    <html>
        <div class="SoaBEf">
            <a href="https://example.com/article1">Link</a>
            <div class="MBeuO">Test Title</div>
            <div class="GI74Re">Test snippet content</div>
            <div class="LfVVr">Jan 15, 2024</div>
            <div class="NUnG9d"><span>Test Source</span></div>
        </div>
    </html>
    """
    mock_make_request.return_value = mock_response

    # Test the function
    results = fetch_news_data('test query', '2024-01-01', '2024-01-31')

    assert len(results) == 1
    assert results[0]['title'] == 'Test Title'
    assert results[0]['snippet'] == 'Test snippet content'
    assert results[0]['date'] == 'Jan 15, 2024'
    assert results[0]['source'] == 'Test Source'
    assert results[0]['link'] == 'https://example.com/article1'


def test_fetch_news_data_date_conversion():
    """Test date format conversion in news data fetching."""
    # This test would verify that date format conversion works correctly
    # Implementation would depend on the actual date handling logic
    pass


@patch('trading_bench.fetchers.news_fetcher.make_request')
def test_fetch_news_data_no_results(mock_make_request):
    """Test news data fetching when no results are found."""
    # Mock empty response
    mock_response = Mock()
    mock_response.content = '<html><body></body></html>'
    mock_make_request.return_value = mock_response

    results = fetch_news_data('nonexistent query', '2024-01-01', '2024-01-31')

    assert len(results) == 0


# Price data fetching tests
@patch('trading_bench.fetchers.stock_fetcher.yf.download')
def test_download_price_data_success(mock_download):
    """Test successful price data download."""
    import pandas as pd

    # Mock successful download
    mock_df = pd.DataFrame(
        {
            'Open': [100.0],
            'High': [105.0],
            'Low': [95.0],
            'Close': [102.0],
            'Volume': [1000000],
        },
        index=[pd.Timestamp('2024-01-15')],
    )

    mock_download.return_value = mock_df

    result = _download_price_data('AAPL', '2024-01-01', '2024-01-31', '1d')

    assert not result.empty
    assert len(result) == 1
    mock_download.assert_called_once()


@patch('trading_bench.fetchers.stock_fetcher.yf.download')
def test_download_price_data_empty_result(mock_download):
    """Test price data download with empty result."""
    import pandas as pd

    # Mock empty download
    mock_download.return_value = pd.DataFrame()

    with pytest.raises(RuntimeError, match='No data returned'):
        _download_price_data('INVALID', '2024-01-01', '2024-01-31', '1d')


@patch('trading_bench.fetchers.stock_fetcher._download_price_data')
def test_fetch_stock_data_success(mock_download):
    """Test successful price data fetching with retry logic."""
    import pandas as pd

    # Mock successful download
    mock_df = pd.DataFrame(
        {
            'Open': [100.0, 102.0],
            'High': [105.0, 107.0],
            'Low': [95.0, 97.0],
            'Close': [102.0, 104.0],
            'Volume': [1000000, 1200000],
        },
        index=[pd.Timestamp('2024-01-15'), pd.Timestamp('2024-01-16')],
    )

    mock_download.return_value = mock_df

    result = fetch_stock_data('AAPL', '2024-01-01', '2024-01-31')

    assert isinstance(result, dict)
    assert len(result) == 2
    assert '2024-01-15' in result
    assert '2024-01-16' in result
    assert result['2024-01-15']['open'] == 100.0
    assert result['2024-01-15']['close'] == 102.0


@patch('trading_bench.fetchers.stock_fetcher._download_price_data')
def test_fetch_stock_data_retry_on_failure(mock_download):
    """Test that price data fetching retries on failure."""
    # Mock download to fail twice, then succeed
    mock_download.side_effect = [
        RuntimeError('Network error'),
        RuntimeError('Network error'),
        pd.DataFrame(
            {
                'Open': [100.0],
                'High': [105.0],
                'Low': [95.0],
                'Close': [102.0],
                'Volume': [1000000],
            },
            index=[pd.Timestamp('2024-01-15')],
        ),
    ]

    result = fetch_stock_data('AAPL', '2024-01-01', '2024-01-31')

    assert isinstance(result, dict)
    assert len(result) == 1
    # Should have been called 3 times (2 failures + 1 success)
    assert mock_download.call_count == 3


# Option data fetching tests
@patch('trading_bench.fetchers.stock_fetcher.yf.Ticker')
def test_fetch_option_expirations_success(mock_ticker):
    """Test successful option expirations fetching."""
    # Mock ticker object
    mock_stock = Mock()
    mock_stock.options = ['2024-01-19', '2024-02-16', '2024-03-15']
    mock_ticker.return_value = mock_stock

    result = fetch_option_expirations('AAPL')

    assert result == ['2024-01-19', '2024-02-16', '2024-03-15']
    mock_ticker.assert_called_once_with('AAPL')


@patch('trading_bench.fetchers.stock_fetcher.yf.Ticker')
def test_fetch_option_expirations_no_options(mock_ticker):
    """Test option expirations fetching when no options available."""
    # Mock ticker object with no options
    mock_stock = Mock()
    mock_stock.options = []
    mock_ticker.return_value = mock_stock

    with pytest.raises(RuntimeError, match='No options available'):
        fetch_option_expirations('INVALID')


@patch('trading_bench.fetchers.stock_fetcher.yf.Ticker')
def test_fetch_option_chain_success(mock_ticker):
    """Test successful option chain fetching."""
    import pandas as pd

    # Mock ticker object
    mock_stock = Mock()
    mock_stock.options = ['2024-01-19', '2024-02-16']
    mock_stock.info = {'regularMarketPrice': 150.0}

    # Mock option chain
    mock_calls = pd.DataFrame(
        {
            'strike': [145.0, 150.0, 155.0],
            'bid': [5.0, 2.5, 0.5],
            'ask': [5.5, 3.0, 1.0],
            'volume': [100, 200, 50],
        }
    )
    mock_puts = pd.DataFrame(
        {
            'strike': [145.0, 150.0, 155.0],
            'bid': [0.5, 2.0, 5.0],
            'ask': [1.0, 2.5, 5.5],
            'volume': [50, 150, 100],
        }
    )

    mock_options = Mock()
    mock_options.calls = mock_calls
    mock_options.puts = mock_puts
    mock_stock.option_chain.return_value = mock_options
    mock_ticker.return_value = mock_stock

    result = fetch_option_chain('AAPL')

    assert result['ticker'] == 'AAPL'
    assert result['expiration'] == '2024-01-19'
    assert result['underlying_price'] == 150.0
    assert len(result['calls']) == 3
    assert len(result['puts']) == 3
    assert result['available_expirations'] == ['2024-01-19', '2024-02-16']


@patch('trading_bench.fetchers.stock_fetcher.yf.Ticker')
def test_fetch_option_data_with_filters(mock_ticker):
    """Test option data fetching with strike filters."""
    import pandas as pd

    # Mock ticker object
    mock_stock = Mock()
    mock_stock.info = {'regularMarketPrice': 150.0}

    # Mock option chain
    mock_calls = pd.DataFrame(
        {
            'strike': [140.0, 145.0, 150.0, 155.0, 160.0],
            'bid': [10.0, 5.0, 2.5, 0.5, 0.1],
            'ask': [10.5, 5.5, 3.0, 1.0, 0.2],
            'volume': [50, 100, 200, 50, 10],
        }
    )
    mock_puts = pd.DataFrame(
        {
            'strike': [140.0, 145.0, 150.0, 155.0, 160.0],
            'bid': [0.1, 0.5, 2.0, 5.0, 10.0],
            'ask': [0.2, 1.0, 2.5, 5.5, 10.5],
            'volume': [10, 50, 150, 100, 50],
        }
    )

    mock_options = Mock()
    mock_options.calls = mock_calls
    mock_options.puts = mock_puts
    mock_stock.option_chain.return_value = mock_options
    mock_ticker.return_value = mock_stock

    # Test with strike filters
    result = fetch_option_data(
        'AAPL', '2024-01-19', option_type='calls', min_strike=145.0, max_strike=155.0
    )

    assert result['ticker'] == 'AAPL'
    assert result['expiration'] == '2024-01-19'
    assert len(result['calls']) == 3  # 145, 150, 155
    assert len(result['puts']) == 0  # Only calls requested


@patch('trading_bench.fetchers.stock_fetcher.yf.download')
def test_fetch_option_historical_data_success(mock_download):
    """Test successful historical option data fetching."""
    import pandas as pd

    # Mock historical data download
    mock_df = pd.DataFrame(
        {
            'Open': [5.0, 5.5, 6.0],
            'High': [5.5, 6.0, 6.5],
            'Low': [4.8, 5.2, 5.8],
            'Close': [5.2, 5.8, 6.2],
            'Volume': [100, 150, 200],
        },
        index=[
            pd.Timestamp('2024-01-15'),
            pd.Timestamp('2024-01-16'),
            pd.Timestamp('2024-01-17'),
        ],
    )

    mock_download.return_value = mock_df

    result = fetch_option_historical_data(
        'AAPL', '2024-01-19', 150.0, 'call', '2024-01-15', '2024-01-17'
    )

    assert result['ticker'] == 'AAPL'
    assert result['expiration'] == '2024-01-19'
    assert result['strike'] == 150.0
    assert result['option_type'] == 'call'
    assert len(result['price_data']) == 3
    assert '2024-01-15' in result['price_data']


def test_calculate_option_greeks():
    """Test option Greeks calculation."""
    # Test call option Greeks
    greeks = calculate_option_greeks(
        underlying_price=100.0,
        strike=100.0,
        time_to_expiry=0.25,  # 3 months
        risk_free_rate=0.05,  # 5%
        volatility=0.3,  # 30%
        option_type='call',
    )

    assert 'delta' in greeks
    assert 'gamma' in greeks
    assert 'theta' in greeks
    assert 'vega' in greeks
    assert 'rho' in greeks

    # Delta should be between 0 and 1 for call options
    assert 0 < greeks['delta'] < 1

    # Gamma should be positive
    assert greeks['gamma'] > 0

    # Test put option Greeks
    put_greeks = calculate_option_greeks(
        underlying_price=100.0,
        strike=100.0,
        time_to_expiry=0.25,
        risk_free_rate=0.05,
        volatility=0.3,
        option_type='put',
    )

    # Delta should be between -1 and 0 for put options
    assert -1 < put_greeks['delta'] < 0


# Polymarket data fetching tests
@patch('trading_bench.fetchers.polymarket_fetcher.requests.get')
def test_fetch_polymarket_markets_success(mock_get):
    """Test successful Polymarket markets fetching."""
    # Mock response
    mock_response = Mock()
    mock_response.json.return_value = [
        {
            'id': 'market1',
            'title': 'Test Market 1',
            'category': 'politics',
            'description': 'Test description',
            'endDate': '2024-12-31',
            'status': 'active',
            'totalVolume': 1000,
            'totalLiquidity': 500,
        },
        {
            'id': 'market2',
            'title': 'Test Market 2',
            'category': 'sports',
            'description': 'Test description 2',
            'endDate': '2024-11-30',
            'status': 'active',
            'totalVolume': 2000,
            'totalLiquidity': 1000,
        },
    ]
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = fetch_polymarket_markets(category='politics', limit=10)

    assert len(result) == 1  # Only politics category
    assert result[0]['id'] == 'market1'
    assert result[0]['category'] == 'politics'
    mock_get.assert_called_once()


@patch('trading_bench.fetchers.polymarket_fetcher.requests.get')
def test_fetch_polymarket_market_details_success(mock_get):
    """Test successful Polymarket market details fetching."""
    # Mock response
    mock_response = Mock()
    mock_response.json.return_value = {
        'id': 'market1',
        'title': 'Test Market',
        'description': 'Test description',
        'category': 'politics',
        'status': 'active',
        'endDate': '2024-12-31',
        'totalVolume': 1000,
        'totalLiquidity': 500,
        'outcomes': [
            {
                'id': 'outcome1',
                'name': 'Yes',
                'currentPrice': 0.6,
                'volume24h': 100,
                'liquidity': 50,
                'probability': 60.0,
            },
            {
                'id': 'outcome2',
                'name': 'No',
                'currentPrice': 0.4,
                'volume24h': 80,
                'liquidity': 40,
                'probability': 40.0,
            },
        ],
    }
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = fetch_polymarket_market_details('market1')

    assert result['id'] == 'market1'
    assert result['title'] == 'Test Market'
    assert len(result['outcomes']) == 2
    assert result['outcomes'][0]['name'] == 'Yes'
    assert result['outcomes'][0]['currentPrice'] == 0.6


@patch('trading_bench.fetchers.polymarket_fetcher.requests.get')
def test_fetch_polymarket_trades_success(mock_get):
    """Test successful Polymarket trades fetching."""
    # Mock response
    mock_response = Mock()
    mock_response.json.return_value = [
        {
            'id': 'trade1',
            'outcomeId': 'outcome1',
            'price': 0.6,
            'size': 100,
            'side': 'buy',
            'timestamp': '2024-01-15T10:00:00Z',
            'maker': 'user1',
            'taker': 'user2',
        },
        {
            'id': 'trade2',
            'outcomeId': 'outcome1',
            'price': 0.65,
            'size': 50,
            'side': 'sell',
            'timestamp': '2024-01-15T09:00:00Z',
            'maker': 'user3',
            'taker': 'user4',
        },
    ]
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = fetch_polymarket_trades('market1', limit=10)

    assert len(result) == 2
    assert result[0]['id'] == 'trade1'
    assert result[0]['side'] == 'buy'
    assert result[1]['side'] == 'sell'


@patch('trading_bench.fetchers.polymarket_fetcher.fetch_polymarket_market_details')
@patch('trading_bench.fetchers.polymarket_fetcher.fetch_polymarket_trades')
def test_fetch_polymarket_market_stats_success(mock_trades, mock_details):
    """Test successful Polymarket market stats fetching."""
    # Mock market details
    mock_details.return_value = {
        'id': 'market1',
        'title': 'Test Market',
        'totalVolume': 1000,
        'totalLiquidity': 500,
        'outcomes': [{'id': 'outcome1'}, {'id': 'outcome2'}],
    }

    # Mock trades
    mock_trades.return_value = [
        {'price': 0.6, 'size': 100},
        {'price': 0.65, 'size': 50},
        {'price': 0.7, 'size': 75},
    ]

    result = fetch_polymarket_market_stats('market1')

    assert result['market_id'] == 'market1'
    assert result['title'] == 'Test Market'
    assert result['total_volume_24h'] == 225  # 100 + 50 + 75
    assert result['outcomes_count'] == 2


def test_search_polymarket_markets():
    """Test Polymarket market search functionality."""
    # Mock markets data
    mock_markets = [
        {
            'title': 'Election 2024',
            'description': 'Presidential election',
            'category': 'politics',
        },
        {
            'title': 'Bitcoin Price',
            'description': 'Crypto prediction',
            'category': 'crypto',
        },
        {
            'title': 'World Cup Winner',
            'description': 'Sports prediction',
            'category': 'sports',
        },
    ]

    with patch(
        'trading_bench.fetchers.polymarket_fetcher.fetch_polymarket_markets',
        return_value=mock_markets,
    ):
        # Test search for election
        results = search_polymarket_markets('election')
        assert len(results) == 1
        assert 'Election' in results[0]['title']

        # Test search for bitcoin
        results = search_polymarket_markets('bitcoin')
        assert len(results) == 1
        assert 'Bitcoin' in results[0]['title']


def test_fetch_polymarket_trending_markets():
    """Test Polymarket trending markets fetching."""
    # Mock markets data
    mock_markets = [
        {'title': 'Market 1', 'total_volume': 1000},
        {'title': 'Market 2', 'total_volume': 2000},
        {'title': 'Market 3', 'total_volume': 500},
    ]

    with patch(
        'trading_bench.fetchers.polymarket_fetcher.fetch_polymarket_markets',
        return_value=mock_markets,
    ):
        result = fetch_polymarket_trending_markets(limit=2)

        assert len(result) == 2
        # Should be sorted by volume (descending)
        assert result[0]['total_volume'] == 2000
        assert result[1]['total_volume'] == 1000


if __name__ == '__main__':
    pytest.main([__file__])

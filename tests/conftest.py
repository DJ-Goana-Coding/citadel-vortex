"""Test fixtures and mock data for testing."""
import pytest
import pandas as pd
from datetime import datetime, timedelta


@pytest.fixture
def sample_ohlcv_bullish():
    """Generate bullish OHLCV data for testing."""
    data = []
    base_price = 100
    for i in range(100):
        timestamp = 1640000000000 + i * 900000  # 15-minute intervals
        open_price = base_price + i * 0.5
        high_price = open_price + 2
        low_price = open_price - 1
        close_price = open_price + 1.5
        volume = 1000000 + i * 10000

        data.append([timestamp, open_price, high_price, low_price, close_price, volume])

    return data


@pytest.fixture
def sample_ohlcv_bearish():
    """Generate bearish OHLCV data for testing."""
    data = []
    base_price = 200
    for i in range(100):
        timestamp = 1640000000000 + i * 900000
        open_price = base_price - i * 0.5
        high_price = open_price + 1
        low_price = open_price - 2
        close_price = open_price - 1.5
        volume = 1000000 + i * 10000

        data.append([timestamp, open_price, high_price, low_price, close_price, volume])

    return data


@pytest.fixture
def sample_ohlcv_sideways():
    """Generate sideways/ranging OHLCV data for testing."""
    data = []
    base_price = 150
    for i in range(100):
        timestamp = 1640000000000 + i * 900000
        open_price = base_price + (i % 10 - 5) * 0.2  # Small oscillations
        high_price = open_price + 1
        low_price = open_price - 1
        close_price = open_price + 0.1
        volume = 1000000

        data.append([timestamp, open_price, high_price, low_price, close_price, volume])

    return data


@pytest.fixture
def sample_dataframe_with_indicators():
    """Generate a DataFrame with technical indicators already calculated."""
    data = {
        't': [1640000000000 + i * 900000 for i in range(100)],
        'o': [100 + i * 0.5 for i in range(100)],
        'h': [102 + i * 0.5 for i in range(100)],
        'l': [99 + i * 0.5 for i in range(100)],
        'c': [101 + i * 0.5 for i in range(100)],
        'v': [1000000 + i * 1000 for i in range(100)],
    }
    df = pd.DataFrame(data)

    # Add mock indicators
    df['EMA50'] = df['c'] * 0.95  # EMA slightly below close
    df['ADX_14'] = [30 + i * 0.1 for i in range(100)]  # Increasing ADX

    return df


@pytest.fixture
def mock_vault_response():
    """Mock response for vault deposit."""
    return {
        'status': 'success',
        'amount': 100.50,
        'timestamp': datetime.now().isoformat()
    }


@pytest.fixture
def mock_exchange_info():
    """Mock exchange information."""
    return {
        'symbols': [
            {
                'symbol': 'SOLUSDT',
                'status': 'TRADING',
                'baseAsset': 'SOL',
                'quoteAsset': 'USDT'
            },
            {
                'symbol': 'BTCUSDT',
                'status': 'TRADING',
                'baseAsset': 'BTC',
                'quoteAsset': 'USDT'
            }
        ]
    }


@pytest.fixture
def mock_market_data():
    """Mock current market data for a symbol."""
    return {
        'symbol': 'SOL/USDT',
        'last': 150.50,
        'bid': 150.45,
        'ask': 150.55,
        'volume': 10000000,
        'timestamp': datetime.now().timestamp() * 1000
    }


@pytest.fixture
def environment_variables():
    """Mock environment variables for testing."""
    return {
        'BINANCE_API_KEY': 'test_api_key_123',
        'BINANCE_API_SECRET': 'test_secret_456',
        'HUB_URL': 'https://test.hub.example.com',
        'CITADEL_SECRET': 'test_citadel_token_789',
        'SYMBOL_LIST': 'SOL/USDT,BTC/USDT,ETH/USDT'
    }

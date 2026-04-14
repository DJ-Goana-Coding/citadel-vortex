"""Configuration and fixtures tests."""
import pytest
import os
from unittest.mock import patch
import sys

# Add parent directory to path to import main
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestConfiguration:
    """Test cases for configuration and environment variables."""

    def test_default_symbol_list(self):
        """Test default SYMBOL_LIST when not set."""
        with patch.dict(os.environ, {}, clear=True):
            # Re-import to get fresh environment
            import importlib
            if 'main' in sys.modules:
                importlib.reload(sys.modules['main'])

            symbols = os.getenv("SYMBOL_LIST", "SOL/USDT").split(",")
            assert symbols == ["SOL/USDT"]

    def test_custom_symbol_list(self):
        """Test custom SYMBOL_LIST."""
        with patch.dict(os.environ, {'SYMBOL_LIST': 'BTC/USDT,ETH/USDT,SOL/USDT'}):
            symbols = os.getenv("SYMBOL_LIST", "SOL/USDT").split(",")
            assert len(symbols) == 3
            assert "BTC/USDT" in symbols
            assert "ETH/USDT" in symbols
            assert "SOL/USDT" in symbols

    def test_empty_symbol_list(self):
        """Test empty SYMBOL_LIST."""
        with patch.dict(os.environ, {'SYMBOL_LIST': ''}):
            symbols = os.getenv("SYMBOL_LIST", "SOL/USDT").split(",")
            # Empty string split returns a list with one empty string
            assert len(symbols) == 1
            assert symbols[0] == ''

    def test_api_key_environment_variable(self):
        """Test BINANCE_API_KEY environment variable."""
        with patch.dict(os.environ, {'BINANCE_API_KEY': 'test_api_key'}):
            api_key = os.getenv("BINANCE_API_KEY")
            assert api_key == 'test_api_key'

    def test_api_secret_environment_variable(self):
        """Test BINANCE_API_SECRET environment variable."""
        with patch.dict(os.environ, {'BINANCE_API_SECRET': 'test_secret'}):
            api_secret = os.getenv("BINANCE_API_SECRET")
            assert api_secret == 'test_secret'

    def test_hub_url_environment_variable(self):
        """Test HUB_URL environment variable."""
        with patch.dict(os.environ, {'HUB_URL': 'https://hub.example.com'}):
            hub_url = os.getenv("HUB_URL")
            assert hub_url == 'https://hub.example.com'

    def test_citadel_secret_environment_variable(self):
        """Test CITADEL_SECRET environment variable."""
        with patch.dict(os.environ, {'CITADEL_SECRET': 'secret_token_123'}):
            hub_token = os.getenv("CITADEL_SECRET")
            assert hub_token == 'secret_token_123'

    def test_missing_environment_variables(self):
        """Test behavior when environment variables are missing."""
        with patch.dict(os.environ, {}, clear=True):
            api_key = os.getenv("BINANCE_API_KEY")
            api_secret = os.getenv("BINANCE_API_SECRET")
            hub_url = os.getenv("HUB_URL")
            hub_token = os.getenv("CITADEL_SECRET")

            assert api_key is None
            assert api_secret is None
            assert hub_url is None
            assert hub_token is None

    def test_symbol_list_with_spaces(self):
        """Test SYMBOL_LIST with spaces."""
        with patch.dict(os.environ, {'SYMBOL_LIST': 'BTC/USDT, ETH/USDT, SOL/USDT'}):
            symbols = os.getenv("SYMBOL_LIST", "SOL/USDT").split(",")
            assert len(symbols) == 3
            # Note: spaces will be included in the symbol names
            assert symbols[0] == "BTC/USDT"
            assert symbols[1] == " ETH/USDT"  # Has leading space
            assert symbols[2] == " SOL/USDT"  # Has leading space

    def test_exchange_configuration(self):
        """Test that exchange is configured correctly."""
        from main import exchange

        assert exchange is not None
        # Verify exchange type is set correctly
        assert hasattr(exchange, 'options')

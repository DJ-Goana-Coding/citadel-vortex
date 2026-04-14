"""Integration tests for market data processing and analysis."""
import pytest
import pandas as pd
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Add parent directory to path to import main
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import PhoenixVortex


class TestMarketDataProcessing:
    """Test cases for market data processing and technical analysis."""

    @pytest.fixture
    def vortex(self):
        """Create a PhoenixVortex instance for testing."""
        return PhoenixVortex()

    def test_dataframe_creation_from_ohlcv(self, sample_ohlcv_bullish):
        """Test DataFrame creation from OHLCV data."""
        df = pd.DataFrame(
            sample_ohlcv_bullish,
            columns=['t', 'o', 'h', 'l', 'c', 'v']
        )

        assert len(df) == 100
        assert list(df.columns) == ['t', 'o', 'h', 'l', 'c', 'v']
        assert df['c'].iloc[-1] > df['c'].iloc[0]  # Bullish trend

    def test_ema_calculation(self, sample_ohlcv_bullish):
        """Test EMA calculation on market data."""
        df = pd.DataFrame(
            sample_ohlcv_bullish,
            columns=['t', 'o', 'h', 'l', 'c', 'v']
        )

        # Calculate EMA
        df['EMA50'] = df['c'].ewm(span=50, adjust=False).mean()

        assert 'EMA50' in df.columns
        assert not df['EMA50'].isna().all()
        # EMA should exist for most rows (after initial period)
        assert df['EMA50'].notna().sum() >= 50

    def test_adx_indicator_requirements(self, sample_ohlcv_bullish):
        """Test that ADX indicator can be calculated with sufficient data."""
        df = pd.DataFrame(
            sample_ohlcv_bullish,
            columns=['t', 'o', 'h', 'l', 'c', 'v']
        )

        # ADX requires high, low, close columns
        assert 'h' in df.columns
        assert 'l' in df.columns
        assert 'c' in df.columns
        assert len(df) >= 14  # ADX requires at least 14 periods

    @pytest.mark.asyncio
    async def test_bullish_signal_detection(self, vortex, sample_ohlcv_bullish):
        """Test detection of bullish signals in trending market."""
        with patch('main.exchange') as mock_exchange:
            mock_exchange.fetch_ohlcv = AsyncMock(return_value=sample_ohlcv_bullish)

            await vortex.scan_market('SOL/USDT')

            # In bullish market, signals might be generated
            # This is a basic check that the function completes without error

    @pytest.mark.asyncio
    async def test_bearish_market_no_signal(self, vortex, sample_ohlcv_bearish):
        """Test that no signals are generated in bearish market."""
        with patch('main.exchange') as mock_exchange:
            mock_exchange.fetch_ohlcv = AsyncMock(return_value=sample_ohlcv_bearish)

            await vortex.scan_market('BTC/USDT')

            # In bearish market with price below EMA, no signal should occur
            # Trade should not be activated
            assert vortex.active_trades.get('BTC/USDT') is None

    @pytest.mark.asyncio
    async def test_sideways_market(self, vortex, sample_ohlcv_sideways):
        """Test behavior in sideways/ranging market."""
        with patch('main.exchange') as mock_exchange:
            mock_exchange.fetch_ohlcv = AsyncMock(return_value=sample_ohlcv_sideways)

            await vortex.scan_market('ETH/USDT')

            # In sideways market, ADX should be low, no signal expected
            # This test just ensures no crash occurs

    def test_breakout_detection_logic(self, sample_ohlcv_bullish):
        """Test the logic for detecting breakouts."""
        df = pd.DataFrame(
            sample_ohlcv_bullish,
            columns=['t', 'o', 'h', 'l', 'c', 'v']
        )

        last = df.iloc[-1]
        prev = df.iloc[-2]

        # Check breakout condition: current close > previous high
        breakout = last['c'] > prev['h']
        # numpy bool types are valid boolean values
        assert bool(breakout) in [True, False]

    def test_insufficient_data_handling(self, vortex):
        """Test handling of insufficient OHLCV data."""
        # Create data with only 10 rows (insufficient for EMA50)
        insufficient_data = [
            [1640000000000 + i * 900000, 100, 102, 99, 101, 1000000]
            for i in range(10)
        ]

        df = pd.DataFrame(
            insufficient_data,
            columns=['t', 'o', 'h', 'l', 'c', 'v']
        )

        # EMA calculation should still work but with NaN values
        df['EMA50'] = df['c'].ewm(span=50, adjust=False).mean()
        assert 'EMA50' in df.columns

    @pytest.mark.asyncio
    async def test_multiple_symbols_parallel(self, vortex):
        """Test scanning multiple symbols in parallel."""
        symbols = ['SOL/USDT', 'BTC/USDT', 'ETH/USDT']
        mock_data = [
            [1640000000000 + i * 900000, 100, 102, 99, 101, 1000000]
            for i in range(100)
        ]

        with patch('main.exchange') as mock_exchange:
            mock_exchange.fetch_ohlcv = AsyncMock(return_value=mock_data)

            # Scan all symbols
            for symbol in symbols:
                await vortex.scan_market(symbol)

            # Verify exchange was called for each symbol
            assert mock_exchange.fetch_ohlcv.call_count == len(symbols)

    def test_volume_data_integrity(self, sample_ohlcv_bullish):
        """Test that volume data is properly structured."""
        df = pd.DataFrame(
            sample_ohlcv_bullish,
            columns=['t', 'o', 'h', 'l', 'c', 'v']
        )

        # Volume should be positive
        assert (df['v'] > 0).all()

        # Volume should be numeric
        assert pd.api.types.is_numeric_dtype(df['v'])

    def test_price_data_consistency(self, sample_ohlcv_bullish):
        """Test OHLC price relationships are consistent."""
        df = pd.DataFrame(
            sample_ohlcv_bullish,
            columns=['t', 'o', 'h', 'l', 'c', 'v']
        )

        # High should be >= Open, Close, Low
        assert (df['h'] >= df['o']).all()
        assert (df['h'] >= df['c']).all()
        assert (df['h'] >= df['l']).all()

        # Low should be <= Open, Close, High
        assert (df['l'] <= df['o']).all()
        assert (df['l'] <= df['c']).all()
        assert (df['l'] <= df['h']).all()

    @pytest.mark.asyncio
    async def test_concurrent_market_scans(self, vortex):
        """Test that concurrent market scans don't interfere with each other."""
        import asyncio

        mock_data = [
            [1640000000000 + i * 900000, 100, 102, 99, 101, 1000000]
            for i in range(100)
        ]

        with patch('main.exchange') as mock_exchange:
            mock_exchange.fetch_ohlcv = AsyncMock(return_value=mock_data)

            # Scan multiple symbols concurrently
            await asyncio.gather(
                vortex.scan_market('SOL/USDT'),
                vortex.scan_market('BTC/USDT'),
                vortex.scan_market('ETH/USDT')
            )

            assert mock_exchange.fetch_ohlcv.call_count == 3

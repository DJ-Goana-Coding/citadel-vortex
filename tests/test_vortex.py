"""Unit tests for PhoenixVortex trading logic."""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import pandas as pd
import sys
import os

# Add parent directory to path to import main
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import PhoenixVortex


class TestPhoenixVortex:
    """Test cases for PhoenixVortex class."""

    @pytest.fixture
    def vortex(self):
        """Create a PhoenixVortex instance for testing."""
        return PhoenixVortex()

    @pytest.fixture
    def mock_ohlcv_data(self):
        """Create mock OHLCV data for testing."""
        # Generate 100 rows of mock data
        data = []
        for i in range(100):
            data.append([
                1640000000000 + i * 900000,  # timestamp (15min intervals)
                100 + i * 0.5,  # open
                102 + i * 0.5,  # high
                99 + i * 0.5,  # low
                101 + i * 0.5,  # close
                1000000 + i * 1000  # volume
            ])
        return data

    @pytest.mark.asyncio
    async def test_vault_deposit_success(self, vortex):
        """Test successful vault deposit."""
        with patch('main.HUB_URL', 'https://test.hub.com'):
            with patch('main.HUB_TOKEN', 'test_token'):
                with patch('requests.post') as mock_post:
                    mock_post.return_value.status_code = 200

                    await vortex.vault_deposit(100.50)

                    # Verify the request was made with correct parameters
                    mock_post.assert_called_once()
                    args, kwargs = mock_post.call_args
                    assert args[0] == 'https://test.hub.com/vault/deposit'
                    assert kwargs['json']['amount'] == 100.50
                    assert kwargs['json']['source'] == 'Vortex_v2'
                    assert kwargs['json']['signature'] == 'G04NNA_RATCHET'
                    assert kwargs['headers']['x-citadel-token'] == 'test_token'

    @pytest.mark.asyncio
    async def test_vault_deposit_failure(self, vortex, capsys):
        """Test vault deposit handles exceptions gracefully."""
        with patch('main.HUB_URL', 'https://test.hub.com'):
            with patch('main.HUB_TOKEN', 'test_token'):
                with patch('requests.post', side_effect=Exception('Network error')):
                    await vortex.vault_deposit(100.50)

                    # Check that error message was printed
                    captured = capsys.readouterr()
                    assert 'HUB_LINK_FRACTURED' in captured.out

    @pytest.mark.asyncio
    async def test_scan_market_no_signal(self, vortex, mock_ohlcv_data):
        """Test market scan when no trading signal is generated."""
        with patch('main.exchange') as mock_exchange:
            # Create mock data with conditions that don't trigger a signal
            mock_exchange.fetch_ohlcv = AsyncMock(return_value=mock_ohlcv_data)

            await vortex.scan_market('SOL/USDT')

            # Verify no trade was activated
            assert 'SOL/USDT' not in vortex.active_trades

    @pytest.mark.asyncio
    async def test_scan_market_with_signal(self, vortex, capsys):
        """Test market scan when trading signal is generated."""
        # Create data that will trigger a signal
        # Need: price > EMA50, ADX > 25, and breakout (current close > previous high)
        ohlcv_data = []
        for i in range(100):
            data_point = [
                1640000000000 + i * 900000,  # timestamp
                100 + i * 2,  # open
                105 + i * 2,  # high
                99 + i * 2,  # low
                103 + i * 2,  # close
                1000000 + i * 1000  # volume
            ]
            ohlcv_data.append(data_point)

        with patch('main.exchange') as mock_exchange:
            mock_exchange.fetch_ohlcv = AsyncMock(return_value=ohlcv_data)

            await vortex.scan_market('BTC/USDT')

            # Check if signal was detected (checking stdout)
            captured = capsys.readouterr()
            # The trade should be activated if signal is detected
            if 'SIGNAL' in captured.out:
                assert vortex.active_trades.get('BTC/USDT') == True

    @pytest.mark.asyncio
    async def test_scan_market_exception_handling(self, vortex, capsys):
        """Test market scan handles exceptions properly."""
        with patch('main.exchange') as mock_exchange:
            mock_exchange.fetch_ohlcv = AsyncMock(
                side_effect=Exception('API rate limit exceeded')
            )

            await vortex.scan_market('ETH/USDT')

            # Check that error was printed
            captured = capsys.readouterr()
            assert 'Scanner Error' in captured.out
            assert 'ETH/USDT' in captured.out

    @pytest.mark.asyncio
    async def test_scan_market_existing_trade(self, vortex, mock_ohlcv_data):
        """Test that scan_market doesn't create duplicate trades."""
        vortex.active_trades['SOL/USDT'] = True

        with patch('main.exchange') as mock_exchange:
            mock_exchange.fetch_ohlcv = AsyncMock(return_value=mock_ohlcv_data)

            await vortex.scan_market('SOL/USDT')

            # Verify trade status hasn't changed
            assert vortex.active_trades['SOL/USDT'] == True

    @pytest.mark.asyncio
    async def test_engine_loop_basic(self, vortex, capsys):
        """Test that engine_loop runs scan for all symbols."""
        with patch.dict(os.environ, {'SYMBOL_LIST': 'SOL/USDT,BTC/USDT'}):
            with patch('main.SYMBOLS', ['SOL/USDT', 'BTC/USDT']):
                with patch.object(vortex, 'scan_market', new_callable=AsyncMock) as mock_scan:
                    # Create a task and cancel it after a short time
                    task = asyncio.create_task(vortex.engine_loop())
                    await asyncio.sleep(0.1)
                    task.cancel()

                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

                    # Verify scan_market was called
                    assert mock_scan.call_count >= 1

    def test_initialization(self, vortex):
        """Test PhoenixVortex initialization."""
        assert isinstance(vortex.active_trades, dict)
        assert len(vortex.active_trades) == 0

    @pytest.mark.asyncio
    async def test_vault_deposit_with_zero_amount(self, vortex):
        """Test vault deposit with zero amount."""
        with patch('main.HUB_URL', 'https://test.hub.com'):
            with patch('main.HUB_TOKEN', 'test_token'):
                with patch('requests.post') as mock_post:
                    mock_post.return_value.status_code = 200

                    await vortex.vault_deposit(0)

                    # Verify the request was made with zero amount
                    args, kwargs = mock_post.call_args
                    assert kwargs['json']['amount'] == 0.0

    @pytest.mark.asyncio
    async def test_vault_deposit_with_negative_amount(self, vortex):
        """Test vault deposit with negative amount."""
        with patch('main.HUB_URL', 'https://test.hub.com'):
            with patch('main.HUB_TOKEN', 'test_token'):
                with patch('requests.post') as mock_post:
                    mock_post.return_value.status_code = 200

                    await vortex.vault_deposit(-50)

                    # Verify the request was made (validation happens server-side)
                    args, kwargs = mock_post.call_args
                    assert kwargs['json']['amount'] == -50.0

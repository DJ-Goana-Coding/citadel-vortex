"""Integration tests for FastAPI endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add parent directory to path to import main
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app, vortex


class TestFastAPIEndpoints:
    """Test cases for FastAPI endpoints."""

    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI app."""
        return TestClient(app)

    def test_health_endpoint(self, client):
        """Test the /healthz endpoint returns correct status."""
        with patch('main.SYMBOLS', ['SOL/USDT', 'BTC/USDT']):
            response = client.get("/healthz")

            assert response.status_code == 200
            data = response.json()
            assert 'status' in data
            assert 'symbols' in data
            assert data['status'] == 'Vortex Spinning'
            assert isinstance(data['symbols'], list)

    def test_health_endpoint_with_single_symbol(self, client):
        """Test health endpoint with a single symbol."""
        with patch('main.SYMBOLS', ['SOL/USDT']):
            response = client.get("/healthz")

            assert response.status_code == 200
            data = response.json()
            assert data['symbols'] == ['SOL/USDT']

    def test_health_endpoint_with_empty_symbols(self, client):
        """Test health endpoint with no symbols."""
        with patch('main.SYMBOLS', []):
            response = client.get("/healthz")

            assert response.status_code == 200
            data = response.json()
            assert data['symbols'] == []

    def test_root_endpoint_not_found(self, client):
        """Test that root endpoint returns 404."""
        response = client.get("/")
        assert response.status_code == 404

    def test_invalid_endpoint(self, client):
        """Test that invalid endpoints return 404."""
        response = client.get("/invalid/endpoint")
        assert response.status_code == 404

    def test_health_endpoint_headers(self, client):
        """Test that health endpoint returns correct headers."""
        with patch('main.SYMBOLS', ['SOL/USDT']):
            response = client.get("/healthz")

            assert response.status_code == 200
            assert 'application/json' in response.headers.get('content-type', '')

    def test_health_endpoint_response_structure(self, client):
        """Test the structure of health endpoint response."""
        with patch('main.SYMBOLS', ['SOL/USDT', 'BTC/USDT', 'ETH/USDT']):
            response = client.get("/healthz")

            assert response.status_code == 200
            data = response.json()

            # Check all expected keys are present
            assert set(data.keys()) == {'status', 'symbols'}

            # Check types
            assert isinstance(data['status'], str)
            assert isinstance(data['symbols'], list)
            assert len(data['symbols']) == 3

    @pytest.mark.asyncio
    async def test_startup_event(self):
        """Test that startup event creates the engine loop task."""
        with patch.object(vortex, 'engine_loop', new_callable=AsyncMock) as mock_engine:
            with patch('asyncio.create_task') as mock_create_task:
                # Import and call the startup function
                from main import start_vortex
                await start_vortex()

                # Verify create_task was called
                mock_create_task.assert_called_once()

    def test_method_not_allowed(self, client):
        """Test that POST to health endpoint returns 405."""
        response = client.post("/healthz")
        assert response.status_code == 405

    def test_health_endpoint_multiple_calls(self, client):
        """Test health endpoint can be called multiple times."""
        with patch('main.SYMBOLS', ['SOL/USDT']):
            for _ in range(5):
                response = client.get("/healthz")
                assert response.status_code == 200
                assert response.json()['status'] == 'Vortex Spinning'

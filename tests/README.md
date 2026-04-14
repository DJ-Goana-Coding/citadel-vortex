# Test Suite for Citadel Vortex

This directory contains comprehensive tests for the Citadel Vortex trading application.

## Test Structure

- `test_vortex.py` - Unit tests for the PhoenixVortex class
- `test_api.py` - Integration tests for FastAPI endpoints
- `test_config.py` - Configuration and environment variable tests
- `test_market_data.py` - Market data processing and analysis tests
- `conftest.py` - Shared fixtures and test utilities

## Running Tests

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run All Tests

```bash
pytest
```

### Run with Coverage Report

```bash
pytest --cov=. --cov-report=term-missing
```

### Run Specific Test File

```bash
pytest tests/test_vortex.py
```

### Run Specific Test

```bash
pytest tests/test_vortex.py::TestPhoenixVortex::test_vault_deposit_success
```

### Generate HTML Coverage Report

```bash
pytest --cov=. --cov-report=html
# Open htmlcov/index.html in your browser
```

## Test Coverage

The test suite covers:

1. **PhoenixVortex Class** (test_vortex.py)
   - Vault deposit functionality (success and failure cases)
   - Market scanning logic
   - Signal detection
   - Exception handling
   - Active trade management
   - Engine loop operation

2. **FastAPI Endpoints** (test_api.py)
   - Health check endpoint
   - Response structure validation
   - Error handling (404, 405)
   - Startup event
   - Multiple request handling

3. **Configuration** (test_config.py)
   - Environment variable handling
   - Symbol list parsing
   - Default values
   - Missing configuration handling

4. **Market Data Processing** (test_market_data.py)
   - OHLCV data processing
   - Technical indicator calculation (EMA, ADX)
   - Signal detection in different market conditions
   - Data integrity validation
   - Concurrent operations

## Mocking Strategy

Tests use mocking for external dependencies:
- `ccxt.exchange` - Mocked to avoid real API calls
- `requests.post` - Mocked for vault deposit calls
- Environment variables - Patched for isolation

## Fixtures

Common test fixtures are defined in `conftest.py`:
- `sample_ohlcv_bullish` - Bullish market data
- `sample_ohlcv_bearish` - Bearish market data
- `sample_ohlcv_sideways` - Sideways/ranging market data
- `environment_variables` - Mock environment configuration

## Continuous Integration

Tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest --cov=. --cov-report=xml
```

## Coverage Goals

Target coverage: 80%+ for all modules

Current coverage areas:
- ✅ Core trading logic
- ✅ API endpoints
- ✅ Configuration handling
- ✅ Market data processing
- ✅ Error handling
- ✅ Async operations

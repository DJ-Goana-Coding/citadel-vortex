---
title: Citadel Vortex
emoji: 🌀
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 10000
pinned: false
license: mit
---

# Citadel Vortex

[![Tests and Coverage](https://github.com/DJ-Goana-Coding/citadel-vortex/actions/workflows/test.yml/badge.svg)](https://github.com/DJ-Goana-Coding/citadel-vortex/actions/workflows/test.yml)
![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)
![Coverage](https://img.shields.io/badge/coverage-87%25-brightgreen)
![License](https://img.shields.io/badge/license-MIT-blue)

**Citadel Vortex** is an automated cryptocurrency market‑scanning service built on FastAPI. It continuously monitors a configurable list of trading pairs on Binance Futures, computes technical indicators (EMA, ADX) on 15‑minute candles, and emits momentum signals. A lightweight reporting hook forwards events to an external "Hub" endpoint for bookkeeping.

> ⚠️ **Disclaimer**: This project interacts with live cryptocurrency markets through the Binance API. It is provided for research and educational purposes only and is **not** financial advice. Trade at your own risk and always review strategy logic before enabling real orders.

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Project Layout](#project-layout)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Service](#running-the-service)
- [API](#api)
- [Vortex → Hub Data Flow (Synapse)](#vortex--hub-data-flow-synapse)
- [Testing](#testing)
- [Continuous Integration](#continuous-integration)
- [Deployment to Hugging Face Spaces](#deployment-to-hugging-face-spaces)
- [Security Notes](#security-notes)
- [License](#license)

---

## Features

- 🔎 **Real‑time market scanning** across any comma‑separated list of symbols (default `SOL/USDT`).
- 📈 **Technical analysis** using `pandas_ta` — EMA(50) and ADX(14) on the 15‑minute timeframe.
- ⚡ **Async engine loop** built on `ccxt.pro` and `asyncio`, scanning every 20 seconds.
- 🌐 **FastAPI service** exposing `/healthz` and `/healthz/hub` endpoints suitable for Render, Fly.io, Hugging Face Spaces, or any container host.
- 🛰️ **Synapse Hub publisher** — periodically POSTs detected signals to the mapping‑and‑inventory Hub's `/v1/ingest` endpoint for RAG awareness.
- 🔐 **Environment‑driven configuration** — no secrets in source.
- 🧪 **Comprehensive test suite** — Python 3.10 / 3.11 / 3.12 matrix in CI.

## Architecture

```
                   ┌────────────────────────┐
                   │     Binance Futures    │
                   │  (ccxt.pro websocket)  │
                   └───────────┬────────────┘
                               │ OHLCV (15m)
                               ▼
        ┌──────────────────────────────────────────┐
        │            PhoenixVortex engine          │
        │  • fetch_ohlcv() per symbol              │
        │  • EMA50 + ADX14 (pandas_ta)             │
        │  • Signal rule:                          │
        │      close > EMA50                       │
        │      AND ADX > 25                        │
        │      AND close > previous high           │
        │  • Tracks active_trades per symbol       │
        └──────────────┬──────────────┬────────────┘
                       │              │
         vault_deposit │              │ FastAPI app
                       ▼              ▼
              ┌────────────────┐  ┌──────────────┐
              │   Hub (HTTP)   │  │  /healthz    │
              │  HUB_URL +     │  │  status JSON │
              │  CITADEL_SECRET│  └──────────────┘
              └────────────────┘
```

The application starts the engine as a background task via FastAPI's `startup` event, then serves the HTTP health endpoint on port `10000`.

## Project Layout

```
citadel-vortex/
├── main.py                     # FastAPI app + PhoenixVortex engine
├── requirements.txt            # Runtime + test dependencies
├── pyproject.toml              # pytest + coverage configuration
├── tests/                      # Test suite (see tests/README.md)
│   ├── conftest.py
│   ├── test_api.py
│   ├── test_config.py
│   ├── test_market_data.py
│   └── test_vortex.py
├── .github/workflows/test.yml  # CI: tests + coverage on Python 3.10–3.12
├── push_to_huggingface.sh      # One‑way deploy script to Hugging Face Spaces
├── HUGGINGFACE.md              # Detailed Hugging Face deployment guide
├── COVERAGE_REPORT.md          # Detailed coverage analysis
└── TEST_SUMMARY.md             # Test suite overview
```

## Requirements

- Python **3.10**, **3.11**, or **3.12**
- A Binance account with API credentials (read‑only is sufficient for scanning)
- Network access to Binance and, if used, your Hub endpoint

## Installation

```bash
git clone https://github.com/DJ-Goana-Coding/citadel-vortex.git
cd citadel-vortex
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration

All configuration is supplied via environment variables. Never commit secrets to the repository.

| Variable              | Required | Default      | Description                                                            |
| --------------------- | -------- | ------------ | ---------------------------------------------------------------------- |
| `BINANCE_API_KEY`     | Yes\*    | —            | Binance API key used by `ccxt.pro`.                                    |
| `BINANCE_API_SECRET`  | Yes\*    | —            | Binance API secret.                                                    |
| `HUB_URL`             | No       | —            | Base URL of the reporting Hub. If unset, `vault_deposit` will no‑op.   |
| `CITADEL_SECRET`      | No       | —            | Bearer token sent to the Hub in the `x-citadel-token` header.          |
| `SYMBOL_LIST`         | No       | `SOL/USDT`   | Comma‑separated list of symbols, e.g. `SOL/USDT,BTC/USDT,ETH/USDT`.    |

\* Required for live market data calls; tests mock the exchange and do not require real credentials.

Example:

```bash
export BINANCE_API_KEY="..."
export BINANCE_API_SECRET="..."
export HUB_URL="https://hub.example.com"
export CITADEL_SECRET="..."
export SYMBOL_LIST="SOL/USDT,BTC/USDT"
```

## Running the Service

```bash
python main.py
```

The service listens on `0.0.0.0:10000` by default (matching Render's web‑service port). On startup it schedules the `PhoenixVortex.engine_loop` coroutine, which scans each configured symbol every 20 seconds.

For local development with auto‑reload:

```bash
uvicorn main:app --host 0.0.0.0 --port 10000 --reload
```

## API

### `GET /healthz`

Liveness probe returning the configured symbols.

```bash
curl http://localhost:10000/healthz
```

```json
{ "status": "Vortex Spinning", "symbols": ["SOL/USDT"] }
```

### `GET /healthz/hub`

Verifies connectivity to the central **mapping-and-inventory Hub** configured
via `HUB_URL`. Returns `configured: false` when no hub is configured, otherwise
probes the hub's `/healthz` endpoint and reports the result.

```bash
curl http://localhost:10000/healthz/hub
```

```json
{
  "configured": true,
  "reachable": true,
  "status_code": 200,
  "url": "https://hub.example.com/healthz"
}
```

## Vortex → Hub Data Flow (Synapse)

Vortex acts as a **Market Intelligence Harvester** spoke that feeds the
mapping-and-inventory Hub's RAG index with real-time market awareness.

```
PhoenixVortex.scan_market()
        │  (momentum_breakout detected)
        ▼
HubPublisher.publish_signal()  ──► in-memory buffer (capped, async-safe)
                                          │
                                          │  every HUB_FLUSH_INTERVAL seconds
                                          ▼
                          POST {HUB_URL}/v1/ingest
                          headers: x-citadel-token: $CITADEL_SECRET
                          body:    { source, count, signals: [...] }
```

The publisher is implemented in [`citadel/hub_publisher.py`](./citadel/hub_publisher.py)
and is started automatically alongside the engine loop on FastAPI startup.

| Variable             | Purpose                                              | Default        |
| -------------------- | ---------------------------------------------------- | -------------- |
| `HUB_URL`            | Base URL of the Hub. Empty disables the publisher.   | _unset_        |
| `CITADEL_SECRET`     | Bearer token sent as `x-citadel-token` header.       | _unset_        |
| `HUB_INGEST_PATH`    | Path appended to `HUB_URL` for ingest.               | `/v1/ingest`   |
| `HUB_FLUSH_INTERVAL` | Seconds between buffered batch flushes.              | `30`           |

Each ingested signal has the shape:

```json
{
  "source": "citadel-vortex",
  "symbol": "SOL/USDT",
  "signal_type": "momentum_breakout",
  "timestamp": "2026-04-18T10:30:00+00:00",
  "payload": {
    "close": 152.4,
    "ema50": 148.1,
    "adx": 31.2,
    "prev_high": 151.9,
    "timeframe": "15m"
  }
}
```

Failed POSTs are logged and the batch is re-queued (bounded by `max_buffer`)
so transient Hub outages do not lose recent signals.

## Testing

The project ships with a full pytest suite configured in `pyproject.toml`.

```bash
# Run the full suite with coverage
pytest

# Terminal coverage summary only
pytest --cov=. --cov-report=term-missing

# HTML coverage report (output in ./htmlcov)
pytest --cov=. --cov-report=html
```

See [`TEST_SUMMARY.md`](./TEST_SUMMARY.md) and [`COVERAGE_REPORT.md`](./COVERAGE_REPORT.md) for a full breakdown (42 tests across 4 files, 87% coverage).

## Continuous Integration

Every push and pull request to `main`, `master`, or `develop` runs [`.github/workflows/test.yml`](./.github/workflows/test.yml), which:

1. Installs dependencies on Python 3.10, 3.11, and 3.12.
2. Executes `pytest --cov=. --cov-report=xml --cov-report=term-missing`.
3. Uploads the resulting `coverage.xml` to Codecov.

## Deployment to Hugging Face Spaces

This repository treats GitHub as the source of truth and pushes outward to Hugging Face Spaces; nothing is pulled back. See [`HUGGINGFACE.md`](./HUGGINGFACE.md) for full details.

Quick start:

```bash
export HF_TOKEN="hf_xxx"                              # write‑scoped token
export HF_REPO="DJ-Goana-Coding/citadel-vortex"       # Space under your namespace
./push_to_huggingface.sh
```

The script:

- Reads `HF_TOKEN` from the environment and exits if it is unset.
- Defaults `HF_REPO` to `DJ-Goana-Coding/citadel-vortex` when unset.
- Uses `huggingface_hub.upload_folder` in push‑only mode, ignoring `__pycache__`, `.git`, `htmlcov`, `.coverage`, `*.pyc`, `*.log`, and `.pytest_cache`.
- Performs **no** `git pull`, clone, or other inbound sync — changes flow GitHub → Hugging Face only.

Configure the same Space‑side environment variables listed in [Configuration](#configuration) via the Hugging Face Space settings UI.

## Security Notes

- All credentials (`BINANCE_API_KEY`, `BINANCE_API_SECRET`, `CITADEL_SECRET`, `HF_TOKEN`) are read from environment variables; none are written to disk or committed.
- When running in GitHub Actions, provide `HF_TOKEN` through **repository secrets**, not workflow inputs.
- The reporting call to `HUB_URL` uses a 5‑second timeout and fails closed (logs `HUB_LINK_FRACTURED`) rather than raising.
- Review and harden the `scan_market` strategy before enabling any real order placement — the current logic only flags signals and marks `active_trades`; order submission is intentionally left as a stub.

## License

Released under the [MIT License](https://opensource.org/licenses/MIT).

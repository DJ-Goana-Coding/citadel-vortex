#!/bin/bash
# Script to push repository to Hugging Face Hub

set -e

echo "🚀 Pushing Citadel Vortex to Hugging Face Hub"

# Check if HF_TOKEN is set
if [ -z "$HF_TOKEN" ]; then
    echo "❌ Error: HF_TOKEN environment variable is not set"
    echo "Please set your Hugging Face token:"
    echo "  export HF_TOKEN=your_huggingface_token"
    echo ""
    echo "You can get your token from: https://huggingface.co/settings/tokens"
    exit 1
fi

# Check if HF_REPO is set
if [ -z "$HF_REPO" ]; then
    echo "⚠️  HF_REPO not set, using default: citadel-vortex"
    HF_REPO="citadel-vortex"
fi

# Install huggingface_hub if not already installed
echo "📦 Installing huggingface_hub..."
pip install -q huggingface_hub

# Create a README for Hugging Face if it doesn't exist
if [ ! -f "README_HF.md" ]; then
    echo "📝 Creating Hugging Face README..."
    cat > README_HF.md << 'EOF'
---
title: Citadel Vortex
emoji: 🌀
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
license: mit
---

# Citadel Vortex - Automated Trading System

An automated cryptocurrency trading system built with FastAPI, featuring technical analysis and real-time market scanning.

## Features

- 🔥 Real-time market scanning with configurable symbols
- 📊 Technical indicators (EMA, ADX) for signal generation
- 🚀 FastAPI-based REST API
- 🧪 Comprehensive test suite (87% coverage, 42 tests)
- 🔒 Secure vault integration for profit management

## Test Coverage

This repository includes a comprehensive test suite:
- **42 passing tests** across 4 test files
- **87% code coverage**
- Unit tests, integration tests, and configuration tests
- Automated CI/CD with GitHub Actions

See [COVERAGE_REPORT.md](./COVERAGE_REPORT.md) for detailed coverage analysis.

## Running Tests

```bash
pip install -r requirements.txt
pytest --cov=. --cov-report=term-missing
```

## Configuration

Set the following environment variables:
- `BINANCE_API_KEY`: Your Binance API key
- `BINANCE_API_SECRET`: Your Binance API secret
- `HUB_URL`: Hub endpoint URL
- `CITADEL_SECRET`: Authentication token
- `SYMBOL_LIST`: Comma-separated trading pairs (e.g., "SOL/USDT,BTC/USDT")

## Deployment

```bash
pip install -r requirements.txt
python main.py
```

The API will be available at `http://0.0.0.0:10000`

## Health Check

```bash
curl http://localhost:10000/healthz
```

## License

MIT License
EOF
fi

# Push to Hugging Face
echo "🔄 Pushing to Hugging Face Hub..."
python << EOF
import os
from huggingface_hub import HfApi, create_repo

token = os.getenv("HF_TOKEN")
repo_id = os.getenv("HF_REPO", "citadel-vortex")

api = HfApi()

# Create repository if it doesn't exist
try:
    create_repo(repo_id=repo_id, token=token, repo_type="space", exist_ok=True)
    print(f"✅ Repository created/verified: {repo_id}")
except Exception as e:
    print(f"⚠️  Note: {e}")

# Upload files
print("📤 Uploading files...")
api.upload_folder(
    folder_path=".",
    repo_id=repo_id,
    repo_type="space",
    token=token,
    ignore_patterns=["*.pyc", "__pycache__", ".git", "htmlcov", ".coverage", "*.log", ".pytest_cache"]
)

print(f"✅ Successfully pushed to: https://huggingface.co/spaces/{repo_id}")
EOF

echo ""
echo "🎉 Done! Your repository is now on Hugging Face Hub"
echo "Visit: https://huggingface.co/spaces/$HF_REPO"

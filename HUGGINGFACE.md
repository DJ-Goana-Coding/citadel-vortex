# Hugging Face Integration Guide

This document explains how to push the Citadel Vortex repository to Hugging Face Hub.

## Prerequisites

1. A Hugging Face account (sign up at https://huggingface.co/)
2. A Hugging Face access token with write permissions

## Getting Your Hugging Face Token

1. Go to https://huggingface.co/settings/tokens
2. Click "New token"
3. Give it a name (e.g., "citadel-vortex")
4. Select "write" permissions
5. Copy the token

## Pushing to Hugging Face

### Option 1: Using the Automated Script

```bash
# Set your Hugging Face token
export HF_TOKEN=your_huggingface_token_here

# Optional: Set custom repository name (defaults to "citadel-vortex")
export HF_REPO=your-username/citadel-vortex

# Run the push script
./push_to_huggingface.sh
```

### Option 2: Manual Push

```bash
# Install huggingface_hub
pip install huggingface_hub

# Login to Hugging Face
huggingface-cli login

# Create a new Space (if needed)
huggingface-cli repo create citadel-vortex --type space --space_sdk docker

# Push the repository
huggingface-cli upload citadel-vortex . --repo-type space
```

## What Gets Pushed

The script will push:
- ✅ Source code (`main.py`)
- ✅ Test suite (`tests/`)
- ✅ Requirements (`requirements.txt`)
- ✅ Test configuration (`pyproject.toml`)
- ✅ Coverage report (`COVERAGE_REPORT.md`)
- ✅ Documentation (README files)
- ✅ GitHub workflows (`.github/workflows/`)

The script excludes:
- ❌ Python cache files (`__pycache__/`, `*.pyc`)
- ❌ Git directory (`.git/`)
- ❌ Coverage artifacts (`htmlcov/`, `.coverage`)
- ❌ Test cache (`.pytest_cache/`)

## Viewing Your Repository

After pushing, your repository will be available at:
```
https://huggingface.co/spaces/your-username/citadel-vortex
```

## Setting Up as a Hugging Face Space

If you want to run Citadel Vortex as a Hugging Face Space:

1. The repository includes a `README_HF.md` that will be created automatically
2. Make sure to set up your environment variables in the Space settings:
   - `BINANCE_API_KEY`
   - `BINANCE_API_SECRET`
   - `HUB_URL`
   - `CITADEL_SECRET`
   - `SYMBOL_LIST`

## Continuous Deployment

You can set up automatic deployment to Hugging Face using GitHub Actions:

```yaml
# Add to .github/workflows/deploy-hf.yml
name: Deploy to Hugging Face

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4

    - name: Push to Hugging Face
      env:
        HF_TOKEN: ${{ secrets.HF_TOKEN }}
      run: ./push_to_huggingface.sh
```

Then add your `HF_TOKEN` to GitHub Secrets.

## Test Coverage on Hugging Face

The repository includes comprehensive test coverage:
- 42 passing tests
- 87% code coverage
- Detailed coverage report in `COVERAGE_REPORT.md`

This demonstrates the quality and reliability of the codebase to users viewing your Hugging Face repository.

## Troubleshooting

### "Invalid token" error
- Verify your token has write permissions
- Re-generate your token if it's expired

### "Repository already exists" error
- The script handles this automatically
- You can manually delete the old Space and try again

### Upload fails
- Check your internet connection
- Ensure you have enough space quota on Hugging Face
- Try uploading smaller batches of files

## Next Steps

After pushing to Hugging Face:
1. ✅ Verify all files were uploaded correctly
2. ✅ Update the Space README with your specific configuration
3. ✅ Set up environment variables in Space settings
4. ✅ Test the deployed application
5. ✅ Share your Space with others!

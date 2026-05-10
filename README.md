---
title: Citadel Vortex
emoji: 🚀
colorFrom: blue
colorTo: red
sdk: docker
app_port: 7860
pinned: false
---

Minimal FastAPI service for deployment.

## Local run

```bash
pip install -r requirements.txt
python app.py
```

## Environment

- `HOST` (default: `0.0.0.0`)
- `PORT` (default: `7860`, validated)
- `LOG_LEVEL` (default: `INFO`)

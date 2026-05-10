import logging
import os
from contextlib import suppress

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("citadel_vortex")


def _safe_int_env(name: str, default: int, minimum: int, maximum: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    with suppress(ValueError):
        value = int(raw_value)
        if minimum <= value <= maximum:
            return value

    logger.warning(
        "Invalid %s=%r; falling back to %s",
        name,
        raw_value,
        default,
    )
    return default


app = FastAPI(title="Citadel Vortex")


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "Unhandled %s while serving %s: %s",
        type(exc).__name__,
        request.url.path,
        str(exc),
    )
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})


@app.get("/")
def root() -> dict[str, str]:
    return {"status": "SUCCESS", "message": "TIA Node Active"}


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper())
    host = os.getenv("HOST", "0.0.0.0")
    port = _safe_int_env("PORT", default=7860, minimum=1, maximum=65535)
    uvicorn.run(app, host=host, port=port)

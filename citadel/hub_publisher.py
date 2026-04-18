"""Synapse: Vortex → mapping-and-inventory Hub publisher.

This module pushes summarized market scans and technical-analysis signals
from the Vortex scanner to the central Hub's RAG ingest endpoint
(``{HUB_URL}/v1/ingest``) so the Hub maintains real-time market awareness.

Design goals:
  * Non-blocking for the scanner loop: signals are enqueued and flushed
    periodically by a background task.
  * Safe by default: missing ``HUB_URL`` disables the publisher silently
    instead of raising.
  * Minimal dependencies: uses ``requests`` (already a project dep).
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

DEFAULT_INGEST_PATH = "/v1/ingest"
DEFAULT_HEALTH_PATH = "/healthz"
DEFAULT_TIMEOUT = 5.0
DEFAULT_FLUSH_INTERVAL = 30.0
DEFAULT_MAX_BUFFER = 256
SOURCE_TAG = "citadel-vortex"


class HubPublisher:
    """Buffers signals locally and POSTs them to the Hub's ingest endpoint.

    Parameters
    ----------
    hub_url:
        Base URL of the mapping-and-inventory Hub (e.g.
        ``https://hub.example.com``). If falsy, the publisher becomes a
        no-op so the scanner can run standalone.
    hub_token:
        Optional bearer/citadel token sent with every request as the
        ``x-citadel-token`` header.
    ingest_path:
        Path appended to ``hub_url`` for ingest. Defaults to ``/v1/ingest``.
    flush_interval:
        Seconds between automatic flushes when running ``run_forever``.
    max_buffer:
        Hard cap on buffered signals; oldest are dropped on overflow.
    timeout:
        Per-request HTTP timeout (seconds).
    session:
        Optional pre-configured ``requests.Session`` (mainly for tests).
    """

    def __init__(
        self,
        hub_url: Optional[str],
        hub_token: Optional[str] = None,
        ingest_path: str = DEFAULT_INGEST_PATH,
        flush_interval: float = DEFAULT_FLUSH_INTERVAL,
        max_buffer: int = DEFAULT_MAX_BUFFER,
        timeout: float = DEFAULT_TIMEOUT,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.hub_url = (hub_url or "").rstrip("/")
        self.hub_token = hub_token
        self.ingest_path = "/" + ingest_path.lstrip("/")
        self.flush_interval = max(1.0, float(flush_interval))
        self.max_buffer = max(1, int(max_buffer))
        self.timeout = float(timeout)
        self._session = session or requests.Session()
        self._buffer: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()

    @property
    def enabled(self) -> bool:
        """``True`` when a hub URL is configured."""
        return bool(self.hub_url)

    @property
    def ingest_url(self) -> str:
        return f"{self.hub_url}{self.ingest_path}"

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.hub_token:
            headers["x-citadel-token"] = self.hub_token
        return headers

    async def publish_signal(
        self,
        symbol: str,
        signal_type: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Enqueue a single signal for the next flush."""
        if not self.enabled:
            return
        record = {
            "source": SOURCE_TAG,
            "symbol": symbol,
            "signal_type": signal_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": payload or {},
        }
        async with self._lock:
            self._buffer.append(record)
            if len(self._buffer) > self.max_buffer:
                # Drop oldest to preserve newest market state.
                drop = len(self._buffer) - self.max_buffer
                del self._buffer[:drop]
                logger.warning(
                    "HubPublisher buffer overflow; dropped %d oldest signals",
                    drop,
                )

    async def flush(self) -> bool:
        """POST the buffered signals to the Hub.

        Returns ``True`` if the request succeeded (or there was nothing to
        send), ``False`` if the POST failed. On failure the buffer is
        preserved so the next flush can retry.
        """
        if not self.enabled:
            return True
        async with self._lock:
            if not self._buffer:
                return True
            batch = list(self._buffer)
            self._buffer.clear()

        body = {"source": SOURCE_TAG, "count": len(batch), "signals": batch}
        try:
            response = await asyncio.to_thread(
                self._session.post,
                self.ingest_url,
                json=body,
                headers=self._headers(),
                timeout=self.timeout,
            )
            response.raise_for_status()
            logger.info("Hub ingest accepted %d signals", len(batch))
            return True
        except Exception as exc:  # noqa: BLE001 - network errors vary
            logger.warning("Hub ingest failed (%s); re-queueing %d signals", exc, len(batch))
            async with self._lock:
                # Re-queue at the front, respecting max_buffer.
                self._buffer = (batch + self._buffer)[-self.max_buffer:]
            return False

    async def run_forever(self) -> None:
        """Periodically flush buffered signals until cancelled."""
        if not self.enabled:
            logger.info("HubPublisher disabled (HUB_URL not set); skipping loop")
            return
        logger.info("HubPublisher started → %s every %.1fs", self.ingest_url, self.flush_interval)
        while True:
            try:
                await asyncio.sleep(self.flush_interval)
                await self.flush()
            except asyncio.CancelledError:
                # Best-effort final flush before exit.
                await self.flush()
                raise


def ping_hub(
    hub_url: Optional[str],
    health_path: str = DEFAULT_HEALTH_PATH,
    timeout: float = DEFAULT_TIMEOUT,
    session: Optional[requests.Session] = None,
) -> Dict[str, Any]:
    """Probe the Hub's health endpoint.

    Returns a dict suitable for embedding in a FastAPI health response.
    Never raises — connectivity errors are reported in the result.
    """
    if not hub_url:
        return {"configured": False, "reachable": False, "detail": "HUB_URL not set"}

    base = hub_url.rstrip("/")
    url = f"{base}{'/' + health_path.lstrip('/')}"
    sess = session or requests
    try:
        response = sess.get(url, timeout=timeout)
        return {
            "configured": True,
            "reachable": 200 <= response.status_code < 400,
            "status_code": response.status_code,
            "url": url,
        }
    except Exception as exc:  # noqa: BLE001
        # Log full detail server-side; do not leak exception text to callers.
        logger.warning("Hub health probe to %s failed: %s", url, exc)
        return {
            "configured": True,
            "reachable": False,
            "url": url,
            "detail": "hub health probe failed",
        }


def publisher_from_env() -> HubPublisher:
    """Build a HubPublisher from standard Vortex environment variables."""
    return HubPublisher(
        hub_url=os.getenv("HUB_URL"),
        hub_token=os.getenv("CITADEL_SECRET"),
        ingest_path=os.getenv("HUB_INGEST_PATH", DEFAULT_INGEST_PATH),
        flush_interval=float(os.getenv("HUB_FLUSH_INTERVAL", DEFAULT_FLUSH_INTERVAL)),
    )

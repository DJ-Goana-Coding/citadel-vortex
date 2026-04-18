"""Tests for citadel.hub_publisher (Synapse)."""
import asyncio
from unittest.mock import MagicMock, patch

import pytest

from citadel.hub_publisher import HubPublisher, ping_hub, publisher_from_env


def _mock_session(status_code=200):
    session = MagicMock()
    response = MagicMock()
    response.status_code = status_code
    response.raise_for_status = MagicMock()
    if status_code >= 400:
        response.raise_for_status.side_effect = Exception(f"HTTP {status_code}")
    session.post.return_value = response
    session.get.return_value = response
    return session, response


class TestHubPublisher:
    def test_disabled_when_no_url(self):
        pub = HubPublisher(hub_url=None)
        assert pub.enabled is False

    def test_enabled_when_url_set(self):
        pub = HubPublisher(hub_url="https://hub.example.com")
        assert pub.enabled is True
        assert pub.ingest_url == "https://hub.example.com/v1/ingest"

    def test_ingest_path_normalised(self):
        pub = HubPublisher(hub_url="https://hub/", ingest_path="v1/ingest")
        assert pub.ingest_url == "https://hub/v1/ingest"

    @pytest.mark.asyncio
    async def test_publish_noop_when_disabled(self):
        pub = HubPublisher(hub_url="")
        await pub.publish_signal("SOL/USDT", "momentum_breakout", {"close": 1.0})
        # Buffer stays empty when disabled
        assert pub._buffer == []

    @pytest.mark.asyncio
    async def test_publish_buffers_signal(self):
        pub = HubPublisher(hub_url="https://hub.example.com")
        await pub.publish_signal("SOL/USDT", "momentum_breakout", {"close": 1.0})
        assert len(pub._buffer) == 1
        rec = pub._buffer[0]
        assert rec["symbol"] == "SOL/USDT"
        assert rec["signal_type"] == "momentum_breakout"
        assert rec["payload"] == {"close": 1.0}
        assert rec["source"] == "citadel-vortex"
        assert "timestamp" in rec

    @pytest.mark.asyncio
    async def test_buffer_overflow_drops_oldest(self):
        pub = HubPublisher(hub_url="https://hub.example.com", max_buffer=3)
        for i in range(5):
            await pub.publish_signal(f"SYM{i}", "x", {})
        assert len(pub._buffer) == 3
        assert [r["symbol"] for r in pub._buffer] == ["SYM2", "SYM3", "SYM4"]

    @pytest.mark.asyncio
    async def test_flush_posts_to_hub(self):
        session, response = _mock_session(200)
        pub = HubPublisher(
            hub_url="https://hub.example.com",
            hub_token="tok",
            session=session,
        )
        await pub.publish_signal("SOL/USDT", "momentum_breakout", {"close": 1.0})
        ok = await pub.flush()
        assert ok is True
        session.post.assert_called_once()
        call = session.post.call_args
        assert call.args[0] == "https://hub.example.com/v1/ingest"
        body = call.kwargs["json"]
        assert body["count"] == 1
        assert body["signals"][0]["symbol"] == "SOL/USDT"
        assert call.kwargs["headers"]["x-citadel-token"] == "tok"
        # Buffer cleared after success
        assert pub._buffer == []

    @pytest.mark.asyncio
    async def test_flush_empty_returns_true(self):
        session, _ = _mock_session(200)
        pub = HubPublisher(hub_url="https://hub.example.com", session=session)
        assert await pub.flush() is True
        session.post.assert_not_called()

    @pytest.mark.asyncio
    async def test_flush_disabled_returns_true(self):
        pub = HubPublisher(hub_url=None)
        assert await pub.flush() is True

    @pytest.mark.asyncio
    async def test_flush_failure_requeues(self):
        session, _ = _mock_session(500)
        pub = HubPublisher(hub_url="https://hub.example.com", session=session)
        await pub.publish_signal("SOL/USDT", "x", {})
        ok = await pub.flush()
        assert ok is False
        # Signal preserved for retry
        assert len(pub._buffer) == 1
        assert pub._buffer[0]["symbol"] == "SOL/USDT"

    @pytest.mark.asyncio
    async def test_run_forever_cancels_cleanly(self):
        session, _ = _mock_session(200)
        pub = HubPublisher(
            hub_url="https://hub.example.com",
            session=session,
            flush_interval=1,
        )
        await pub.publish_signal("SOL/USDT", "x", {})
        task = asyncio.create_task(pub.run_forever())
        await asyncio.sleep(0.05)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        # Final flush on cancel emptied the buffer
        assert pub._buffer == []
        session.post.assert_called()


class TestPingHub:
    def test_unconfigured(self):
        result = ping_hub(None)
        assert result == {
            "configured": False,
            "reachable": False,
            "detail": "HUB_URL not set",
        }

    def test_reachable(self):
        session, _ = _mock_session(200)
        result = ping_hub("https://hub.example.com", session=session)
        assert result["configured"] is True
        assert result["reachable"] is True
        assert result["status_code"] == 200
        assert result["url"] == "https://hub.example.com/healthz"

    def test_unreachable(self):
        session = MagicMock()
        session.get.side_effect = Exception("connection refused")
        result = ping_hub("https://hub.example.com", session=session)
        assert result["configured"] is True
        assert result["reachable"] is False
        # Detail is generic — exception text must not leak to callers.
        assert result["detail"] == "hub health probe failed"
        assert "connection refused" not in result["detail"]

    def test_server_error_marks_unreachable(self):
        session, _ = _mock_session(500)
        result = ping_hub("https://hub.example.com", session=session)
        assert result["reachable"] is False

    def test_client_error_marks_unreachable(self):
        session, _ = _mock_session(404)
        result = ping_hub("https://hub.example.com", session=session)
        assert result["reachable"] is False


class TestPublisherFromEnv:
    def test_uses_env_vars(self, monkeypatch):
        monkeypatch.setenv("HUB_URL", "https://env-hub.example.com")
        monkeypatch.setenv("CITADEL_SECRET", "envtok")
        monkeypatch.setenv("HUB_FLUSH_INTERVAL", "5")
        pub = publisher_from_env()
        assert pub.hub_url == "https://env-hub.example.com"
        assert pub.hub_token == "envtok"
        assert pub.flush_interval == 5.0
        assert pub.ingest_url.endswith("/v1/ingest")

    def test_disabled_without_url(self, monkeypatch):
        monkeypatch.delenv("HUB_URL", raising=False)
        pub = publisher_from_env()
        assert pub.enabled is False

"""Feishu (Lark) group bot webhook backend."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import logging
import time

from .base import NotifierBackend
from .formatters import format_feishu_card

logger = logging.getLogger("qmt_bridge.notify.feishu")

# Minimum interval between requests to avoid Feishu rate-limit
_MIN_INTERVAL = 0.5


class FeishuWebhookBackend(NotifierBackend):
    """Send notifications via Feishu custom bot webhook."""

    def __init__(self, webhook_url: str, secret: str = "") -> None:
        self._url = webhook_url
        self._secret = secret
        self._client = None  # type: ignore[assignment]
        self._last_send: float = 0.0
        self._lock = asyncio.Lock()

    def name(self) -> str:
        return "feishu"

    async def start(self) -> None:
        import httpx

        self._client = httpx.AsyncClient(timeout=10.0)

    async def stop(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    def _sign(self, timestamp: str) -> str:
        """Compute Feishu v2 HMAC-SHA256 signature."""
        string_to_sign = f"{timestamp}\n{self._secret}"
        hmac_code = hmac.new(
            string_to_sign.encode("utf-8"),
            msg=b"",
            digestmod=hashlib.sha256,
        ).digest()
        return base64.b64encode(hmac_code).decode("utf-8")

    async def send(self, event: dict) -> None:
        if self._client is None:
            logger.warning("Feishu client not started, dropping event")
            return

        async with self._lock:
            # Rate-limit: wait if needed
            now = time.monotonic()
            elapsed = now - self._last_send
            if elapsed < _MIN_INTERVAL:
                await asyncio.sleep(_MIN_INTERVAL - elapsed)

            body = format_feishu_card(event)

            # Add signature if secret is configured
            if self._secret:
                timestamp = str(int(time.time()))
                body["timestamp"] = timestamp
                body["sign"] = self._sign(timestamp)

            resp = await self._client.post(self._url, json=body)
            self._last_send = time.monotonic()

        if resp.status_code != 200:
            logger.warning(
                "Feishu webhook returned %s: %s", resp.status_code, resp.text
            )
        else:
            try:
                data = resp.json()
            except Exception:
                logger.warning("Feishu returned non-JSON response: %s", resp.text[:200])
                return
            if data.get("code", 0) != 0:
                logger.warning("Feishu API error: %s", data)

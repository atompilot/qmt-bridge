"""Generic HTTP webhook backend — POST event JSON to any URL."""

from __future__ import annotations

import logging

from .base import NotifierBackend

logger = logging.getLogger("qmt_bridge.notify.webhook")


class GenericWebhookBackend(NotifierBackend):
    """Send notifications as JSON POST to a user-configured URL."""

    def __init__(self, webhook_url: str, secret: str = "") -> None:
        self._url = webhook_url
        self._secret = secret
        self._client = None  # type: ignore[assignment]

    def name(self) -> str:
        return "webhook"

    async def start(self) -> None:
        import httpx

        self._client = httpx.AsyncClient(timeout=10.0)

    async def stop(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def send(self, event: dict) -> None:
        if self._client is None:
            logger.warning("Webhook client not started, dropping event")
            return

        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self._secret:
            headers["X-Webhook-Secret"] = self._secret

        resp = await self._client.post(self._url, json=event, headers=headers)
        if resp.status_code >= 400:
            logger.warning(
                "Webhook %s returned %s: %s",
                self._url,
                resp.status_code,
                resp.text[:200],
            )

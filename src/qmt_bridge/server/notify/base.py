"""Abstract notifier backend and manager that dispatches events to backends."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from fastapi import APIRouter, HTTPException, Request

if TYPE_CHECKING:
    from ..config import Settings

logger = logging.getLogger("qmt_bridge.notify")

# ---------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------


class NotifierBackend(ABC):
    """Interface every notification backend must implement."""

    @abstractmethod
    async def start(self) -> None: ...

    @abstractmethod
    async def stop(self) -> None: ...

    @abstractmethod
    async def send(self, event: dict) -> None: ...

    @abstractmethod
    def name(self) -> str: ...


# ---------------------------------------------------------------------
# Manager
# ---------------------------------------------------------------------


class NotifierManager:
    """Manages multiple notifier backends with event filtering."""

    def __init__(self, settings: Settings) -> None:
        self._backends: list[NotifierBackend] = []
        self._allow: set[str] | None = None
        self._deny: set[str] = set()

        # Parse event type filters
        if settings.notify_event_types:
            self._allow = {
                t.strip()
                for t in settings.notify_event_types.split(",")
                if t.strip()
            }
        if settings.notify_ignore_event_types:
            self._deny = {
                t.strip()
                for t in settings.notify_ignore_event_types.split(",")
                if t.strip()
            }

        # Instantiate backends
        backend_names = [
            n.strip()
            for n in settings.notify_backends.split(",")
            if n.strip()
        ]
        for bname in backend_names:
            backend = self._create_backend(bname, settings)
            if backend is not None:
                self._backends.append(backend)

        if not self._backends:
            logger.warning(
                "Notification enabled but no backends configured "
                "(set QMT_BRIDGE_NOTIFY_BACKENDS)"
            )

    @staticmethod
    def _create_backend(
        name: str, settings: Settings
    ) -> NotifierBackend | None:
        if name == "feishu":
            from .feishu import FeishuWebhookBackend

            if not settings.feishu_webhook_url:
                logger.warning("feishu backend requested but FEISHU_WEBHOOK_URL is empty")
                return None
            return FeishuWebhookBackend(
                webhook_url=settings.feishu_webhook_url,
                secret=settings.feishu_webhook_secret,
            )
        if name == "webhook":
            from .webhook import GenericWebhookBackend

            if not settings.webhook_url:
                logger.warning("webhook backend requested but WEBHOOK_URL is empty")
                return None
            return GenericWebhookBackend(
                webhook_url=settings.webhook_url,
                secret=settings.webhook_secret,
            )
        logger.warning("Unknown notify backend: %s", name)
        return None

    @property
    def backend_names(self) -> list[str]:
        return [b.name() for b in self._backends]

    def _should_notify(self, event: dict) -> bool:
        event_type = event.get("type", "")
        if event_type in self._deny:
            return False
        if self._allow is not None and event_type not in self._allow:
            return False
        return True

    async def dispatch(self, event: dict, *, bypass_filter: bool = False) -> None:
        """Send event to all backends (never raises)."""
        if not bypass_filter and not self._should_notify(event):
            return
        for backend in self._backends:
            try:
                await backend.send(event)
            except Exception:
                logger.exception("Notify backend %s failed", backend.name())

    async def start(self) -> None:
        for backend in self._backends:
            try:
                await backend.start()
                logger.info("Notifier backend started: %s", backend.name())
            except Exception:
                logger.exception("Failed to start notifier backend: %s", backend.name())

    async def stop(self) -> None:
        for backend in self._backends:
            try:
                await backend.stop()
                logger.info("Notifier backend stopped: %s", backend.name())
            except Exception:
                logger.exception("Error stopping notifier backend: %s", backend.name())


# ---------------------------------------------------------------------
# Test endpoint
# ---------------------------------------------------------------------

router = APIRouter(prefix="/api/notify", tags=["notify"])


@router.post("/test")
async def test_notify(request: Request):
    """Send a test notification to all configured backends."""
    notifier: NotifierManager | None = getattr(
        request.app.state, "notifier_manager", None
    )
    if notifier is None:
        raise HTTPException(503, "Notification module not enabled")
    test_event = {
        "type": "test",
        "data": {"message": "QMT Bridge notification test"},
    }
    await notifier.dispatch(test_event, bypass_filter=True)
    return {"status": "sent", "backends": notifier.backend_names}

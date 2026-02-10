"""WebSocket endpoint — trade event callbacks /ws/trade."""

import asyncio
import json
import hmac
import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

router = APIRouter()
logger = logging.getLogger("qmt_bridge.ws.trade")

# Connected trade WebSocket clients
_trade_listeners: set[WebSocket] = set()


async def broadcast_trade_event(event: dict):
    """Broadcast a trade event to all connected listeners."""
    dead = set()
    for ws in _trade_listeners:
        try:
            await ws.send_json(event)
        except Exception:
            dead.add(ws)
    _trade_listeners.difference_update(dead)


@router.websocket("/ws/trade")
async def ws_trade(
    ws: WebSocket,
    api_key: str = Query("", alias="api_key"),
):
    """Trade event WebSocket — receives real-time order/trade/error events.

    Authentication is done via query parameter ``api_key``.
    """
    from ..config import get_settings

    settings = get_settings()

    # Authenticate
    if not settings.api_key:
        await ws.close(code=1008, reason="API key not configured on server")
        return
    if not api_key or not hmac.compare_digest(api_key, settings.api_key):
        await ws.close(code=1008, reason="Invalid API key")
        return

    await ws.accept()
    _trade_listeners.add(ws)
    logger.info("Trade WebSocket client connected")

    try:
        while True:
            # Keep-alive; client may send pings
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        _trade_listeners.discard(ws)
        logger.info("Trade WebSocket client disconnected")

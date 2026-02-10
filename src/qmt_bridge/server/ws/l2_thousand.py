"""WebSocket endpoint — L2 thousand-level quote subscription /ws/l2_thousand."""

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from xtquant import xtdata

from ..helpers import _numpy_to_python

router = APIRouter()


@router.websocket("/ws/l2_thousand")
async def ws_l2_thousand(ws: WebSocket):
    """Subscribe to L2 thousand-level (千档) real-time data."""
    await ws.accept()
    seq_ids: list[int] = []
    loop = asyncio.get_event_loop()

    try:
        msg = await ws.receive_text()
        payload = json.loads(msg)
        stocks: list[str] = payload.get("stocks", [])

        async def _send(data):
            try:
                await ws.send_json(data)
            except Exception:
                pass

        def on_data(data):
            clean = _numpy_to_python(data)
            asyncio.run_coroutine_threadsafe(_send(clean), loop)

        for stock in stocks:
            seq = xtdata.subscribe_quote(
                stock_code=stock,
                period="l2thousand",
                callback=on_data,
            )
            seq_ids.append(seq)

        while True:
            await ws.receive_text()

    except WebSocketDisconnect:
        pass
    finally:
        for seq in seq_ids:
            xtdata.unsubscribe_quote(seq)

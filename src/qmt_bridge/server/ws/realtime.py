"""WebSocket endpoint — realtime quote subscription /ws/realtime."""

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from xtquant import xtdata

from ..helpers import _numpy_to_python

router = APIRouter()


@router.websocket("/ws/realtime")
async def ws_realtime(ws: WebSocket):
    await ws.accept()
    seq_ids: list[int] = []
    loop = asyncio.get_event_loop()

    try:
        # Wait for subscription request
        msg = await ws.receive_text()
        payload = json.loads(msg)
        stocks: list[str] = payload.get("stocks", [])
        period: str = payload.get("period", "tick")

        async def _send(data):
            try:
                await ws.send_json(data)
            except Exception:
                pass

        def on_data(data):
            """Callback invoked by xtdata in its own thread."""
            clean = _numpy_to_python(data)
            asyncio.run_coroutine_threadsafe(_send(clean), loop)

        # Subscribe each stock
        for stock in stocks:
            seq = xtdata.subscribe_quote(
                stock_code=stock,
                period=period,
                callback=on_data,
            )
            seq_ids.append(seq)

        # Keep connection alive until client disconnects
        while True:
            await ws.receive_text()

    except WebSocketDisconnect:
        pass
    finally:
        for seq in seq_ids:
            xtdata.unsubscribe_quote(seq)

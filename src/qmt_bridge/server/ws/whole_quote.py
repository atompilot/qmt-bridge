"""WebSocket endpoint — whole market quote subscription /ws/whole_quote."""

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from xtquant import xtdata

from ..helpers import _numpy_to_python

router = APIRouter()


@router.websocket("/ws/whole_quote")
async def ws_whole_quote(ws: WebSocket):
    await ws.accept()
    seq_id = None
    loop = asyncio.get_event_loop()

    try:
        msg = await ws.receive_text()
        payload = json.loads(msg)
        code_list: list[str] = payload.get("codes", [])

        async def _send(data):
            try:
                await ws.send_json(data)
            except Exception:
                pass

        def on_data(data):
            clean = _numpy_to_python(data)
            asyncio.run_coroutine_threadsafe(_send(clean), loop)

        seq_id = xtdata.subscribe_whole_quote(code_list, callback=on_data)

        while True:
            await ws.receive_text()

    except WebSocketDisconnect:
        pass
    finally:
        if seq_id is not None:
            xtdata.unsubscribe_quote(seq_id)

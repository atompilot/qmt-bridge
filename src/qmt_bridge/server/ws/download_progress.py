"""WebSocket endpoint — download progress tracking /ws/download_progress."""

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from xtquant import xtdata

from ..helpers import _numpy_to_python

router = APIRouter()


@router.websocket("/ws/download_progress")
async def ws_download_progress(ws: WebSocket):
    await ws.accept()
    loop = asyncio.get_event_loop()

    try:
        msg = await ws.receive_text()
        payload = json.loads(msg)
        stocks: list[str] = payload.get("stocks", [])
        period: str = payload.get("period", "1d")
        start_time: str = payload.get("start_time", "")
        end_time: str = payload.get("end_time", "")

        async def _send(data):
            try:
                await ws.send_json(data)
            except Exception:
                pass

        def on_progress(data):
            clean = _numpy_to_python(data)
            asyncio.run_coroutine_threadsafe(_send(clean), loop)

        xtdata.download_history_data2(
            stocks,
            period=period,
            start_time=start_time,
            end_time=end_time,
            callback=on_progress,
        )

        await ws.send_json({"status": "done"})

    except WebSocketDisconnect:
        pass

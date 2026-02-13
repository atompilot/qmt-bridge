"""下载进度 WebSocket 端点 — /ws/download_progress。

本模块提供历史数据下载进度的实时跟踪服务。

使用流程：
1. 客户端建立 WebSocket 连接
2. 客户端发送下载参数 JSON：
   {"stocks": ["000001.SZ"], "period": "1d", "start_time": "20230101", "end_time": "20231231"}
3. 服务端调用 download_history_data2_safe 逐只下载
4. 每只股票完成后通过 WebSocket 推送进度
5. 全部完成后发送 {"status": "done", "results": {...}} 并结束
"""

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..downloader import download_history_data2_safe

router = APIRouter()


@router.websocket("/ws/download_progress")
async def ws_download_progress(ws: WebSocket):
    """历史数据下载进度 WebSocket 端点。

    接受客户端的下载请求参数，调用安全下载函数逐只下载历史数据，
    并将逐只进度实时推送给客户端。

    协议：
        客户端发送下载请求 JSON::

            {
                "stocks": ["000001.SZ", "600000.SH"],
                "period": "1d",
                "start_time": "20230101",
                "end_time": "20231231"
            }

        服务端推送逐只下载进度::

            {"finished": 1, "total": 2, "stock": "000001.SZ", "status": "ok"}
            {"finished": 2, "total": 2, "stock": "600000.SH", "status": "ok"}

        全部完成后发送::

            {"status": "done", "results": {"000001.SZ": "ok", "600000.SH": "ok"}}
    """
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
            """异步发送进度数据到 WebSocket 客户端。"""
            try:
                await ws.send_json(data)
            except Exception:
                pass

        def on_progress(data):
            """下载进度回调 — 在线程池线程中被调用。"""
            asyncio.run_coroutine_threadsafe(_send(data), loop)

        # 在线程池中运行，避免阻塞事件循环
        results = await loop.run_in_executor(
            None,
            lambda: download_history_data2_safe(
                stocks, period, start_time, end_time, callback=on_progress,
            ),
        )

        await ws.send_json({"status": "done", "results": results})

    except WebSocketDisconnect:
        pass

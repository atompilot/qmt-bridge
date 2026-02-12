"""下载进度 WebSocket 端点 — /ws/download_progress。

本模块提供历史数据下载进度的实时跟踪服务。

使用流程：
1. 客户端建立 WebSocket 连接
2. 客户端发送下载参数 JSON：
   {"stocks": ["000001.SZ"], "period": "1d", "start_time": "20230101", "end_time": "20231231"}
3. 服务端调用 xtdata.download_history_data2 开始下载
4. 下载进度通过回调实时推送给客户端
5. 下载完成后发送 {"status": "done"} 并结束
"""

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from xtquant import xtdata

from ..helpers import _numpy_to_python

router = APIRouter()


@router.websocket("/ws/download_progress")
async def ws_download_progress(ws: WebSocket):
    """历史数据下载进度 WebSocket 端点。

    接受客户端的下载请求参数，调用 xtdata 下载历史数据，
    并将下载进度实时推送给客户端。

    协议：
        客户端发送下载请求 JSON::

            {
                "stocks": ["000001.SZ", "600000.SH"],
                "period": "1d",
                "start_time": "20230101",
                "end_time": "20231231"
            }

        服务端推送下载进度信息，最终发送::

            {"status": "done"}
    """
    await ws.accept()
    loop = asyncio.get_event_loop()

    try:
        # 接收客户端的下载参数
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
            """下载进度回调 — 在 xtdata 后台线程中被调用。

            将进度数据转换为原生 Python 类型后投递到 asyncio 事件循环。
            """
            clean = _numpy_to_python(data)
            asyncio.run_coroutine_threadsafe(_send(clean), loop)

        # 调用 xtdata 下载历史数据，下载过程中通过回调推送进度
        xtdata.download_history_data2(
            stocks,
            period=period,
            start_time=start_time,
            end_time=end_time,
            callback=on_progress,
        )

        # 下载完成，通知客户端
        await ws.send_json({"status": "done"})

    except WebSocketDisconnect:
        pass

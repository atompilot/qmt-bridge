"""全市场行情 WebSocket 端点 — /ws/whole_quote。

本模块提供全市场行情（整体报价）的 WebSocket 推送服务。

与 realtime 端点逐只股票订阅不同，whole_quote 使用
xtdata.subscribe_whole_quote 批量订阅整个市场或板块的行情，
适用于需要监控大量股票实时报价的场景。

使用流程：
1. 客户端建立 WebSocket 连接
2. 客户端发送订阅请求：{"codes": ["SH", "SZ"]}（市场代码列表）
3. 服务端通过 xtdata.subscribe_whole_quote 订阅全市场行情
4. 行情数据通过回调实时推送给客户端
5. 客户端断开时自动取消订阅
"""

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from xtquant import xtdata

from ..helpers import _numpy_to_python

router = APIRouter()


@router.websocket("/ws/whole_quote")
async def ws_whole_quote(ws: WebSocket):
    """全市场行情 WebSocket 端点。

    接受市场代码列表的订阅请求，推送全市场实时行情数据。

    协议：
        客户端发送订阅请求 JSON::

            {"codes": ["SH", "SZ"]}

        服务端持续推送全市场行情数据，直到客户端断开连接。
    """
    await ws.accept()
    seq_id = None  # 全市场行情订阅的序列号
    loop = asyncio.get_event_loop()

    try:
        # 接收订阅请求
        msg = await ws.receive_text()
        payload = json.loads(msg)
        code_list: list[str] = payload.get("codes", [])

        async def _send(data):
            """异步发送行情数据到 WebSocket 客户端。"""
            try:
                await ws.send_json(data)
            except Exception:
                pass

        def on_data(data):
            """全市场行情回调 — 在 xtdata 后台线程中被调用。

            将行情数据转换后投递到 asyncio 事件循环发送给客户端。
            """
            clean = _numpy_to_python(data)
            asyncio.run_coroutine_threadsafe(_send(clean), loop)

        # 订阅全市场行情
        seq_id = xtdata.subscribe_whole_quote(code_list, callback=on_data)

        # 保持连接存活，等待客户端断开
        while True:
            await ws.receive_text()

    except WebSocketDisconnect:
        pass
    finally:
        # 清理：取消全市场行情订阅
        if seq_id is not None:
            xtdata.unsubscribe_quote(seq_id)

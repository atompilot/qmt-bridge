"""L2 千档行情 WebSocket 端点 — /ws/l2_thousand。

本模块提供 Level-2 千档（逐笔委托）行情数据的实时推送服务。

千档行情提供比普通五档行情更详细的盘口数据（最多 1000 档买卖挂单），
适用于需要深度市场微观结构分析的场景。

注意：L2 千档数据需要 QMT 终端开通 Level-2 行情权限。

使用流程：
1. 客户端建立 WebSocket 连接
2. 客户端发送订阅请求：{"stocks": ["000001.SZ"]}
3. 服务端通过 xtdata.subscribe_quote（period="l2thousand"）订阅千档行情
4. 千档行情数据通过回调实时推送给客户端
5. 客户端断开时自动取消订阅
"""

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from xtquant import xtdata

from ..helpers import _numpy_to_python

router = APIRouter()


@router.websocket("/ws/l2_thousand")
async def ws_l2_thousand(ws: WebSocket):
    """L2 千档行情 WebSocket 端点。

    订阅指定股票的 L2 千档行情数据，实时推送深度盘口信息。

    协议：
        客户端发送订阅请求 JSON::

            {"stocks": ["000001.SZ", "600000.SH"]}

        服务端持续推送千档行情数据，直到客户端断开连接。
    """
    await ws.accept()
    seq_ids: list[int] = []  # 记录订阅序列号，用于断开时取消订阅
    loop = asyncio.get_event_loop()

    try:
        # 接收订阅请求
        msg = await ws.receive_text()
        payload = json.loads(msg)
        stocks: list[str] = payload.get("stocks", [])

        async def _send(data):
            """异步发送千档行情数据到 WebSocket 客户端。"""
            try:
                await ws.send_json(data)
            except Exception:
                pass

        def on_data(data):
            """千档行情回调 — 在 xtdata 后台线程中被调用。

            将行情数据转换后投递到 asyncio 事件循环发送给客户端。
            """
            clean = _numpy_to_python(data)
            asyncio.run_coroutine_threadsafe(_send(clean), loop)

        # 逐只股票订阅千档行情（使用 period="l2thousand"）
        for stock in stocks:
            seq = xtdata.subscribe_quote(
                stock_code=stock,
                period="l2thousand",
                callback=on_data,
            )
            seq_ids.append(seq)

        # 保持连接存活，等待客户端断开
        while True:
            await ws.receive_text()

    except WebSocketDisconnect:
        pass
    finally:
        # 清理：取消所有千档行情订阅
        for seq in seq_ids:
            xtdata.unsubscribe_quote(seq)

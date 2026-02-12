"""实时行情 WebSocket 端点 — /ws/realtime。

本模块提供实时行情数据的 WebSocket 推送服务。

使用流程：
1. 客户端建立 WebSocket 连接
2. 客户端发送 JSON 订阅请求：{"stocks": ["000001.SZ"], "period": "tick"}
3. 服务端通过 xtdata.subscribe_quote 订阅行情
4. xtdata 在后台线程中推送行情数据，通过 asyncio.run_coroutine_threadsafe
   桥接到 WebSocket 发送给客户端
5. 客户端断开连接时自动取消订阅

实时 K 线构建（REST 拉历史 + WS 推增量）：
    period 不仅支持 "tick"，也支持 "1m"/"5m"/"1d" 等 K 线周期。
    subscribe_quote(period="1m") 推送的是 xtdata 聚合好的分钟 K 线柱，
    而非原始 tick，客户端无需自行合成。

    客户端标准用法：
    1. 先调 REST GET /api/market/market_data_ex (period="1m") 拉取历史 K 线
    2. 再连本 WS 端点，订阅相同周期 {"stocks": [...], "period": "1m"}
    3. 收到推送后按时间戳与本地数组末尾比较：
       - 时间戳相同 → 更新最后一根（盘中未完结柱）
       - 时间戳更大 → 追加新柱
"""

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from xtquant import xtdata

from ..helpers import _numpy_to_python

router = APIRouter()


@router.websocket("/ws/realtime")
async def ws_realtime(ws: WebSocket):
    """实时行情 WebSocket 端点。

    接受客户端的行情订阅请求，将 xtdata 推送的实时行情数据转发给客户端。
    支持订阅多只股票，支持 tick/1m/5m/1d 等多种周期。

    协议：
        客户端发送订阅请求 JSON::

            {"stocks": ["000001.SZ", "600000.SH"], "period": "tick"}

        服务端持续推送行情数据 JSON，直到客户端断开连接。
    """
    await ws.accept()
    seq_ids: list[int] = []  # 记录所有订阅的序列号，用于断开时取消订阅
    loop = asyncio.get_event_loop()

    try:
        # 等待客户端发送订阅请求
        msg = await ws.receive_text()
        payload = json.loads(msg)
        stocks: list[str] = payload.get("stocks", [])
        period: str = payload.get("period", "tick")

        async def _send(data):
            """异步发送数据到 WebSocket 客户端（忽略发送失败）。"""
            try:
                await ws.send_json(data)
            except Exception:
                pass

        def on_data(data):
            """xtdata 行情回调 — 在 xtdata 后台线程中被调用。

            将 numpy/pandas 数据转换为原生 Python 类型后，
            通过 run_coroutine_threadsafe 投递到 asyncio 事件循环发送。
            """
            clean = _numpy_to_python(data)
            asyncio.run_coroutine_threadsafe(_send(clean), loop)

        # 逐只股票订阅行情
        for stock in stocks:
            seq = xtdata.subscribe_quote(
                stock_code=stock,
                period=period,
                callback=on_data,
            )
            seq_ids.append(seq)

        # 保持连接存活，等待客户端断开
        while True:
            await ws.receive_text()

    except WebSocketDisconnect:
        pass
    finally:
        # 清理：取消所有行情订阅
        for seq in seq_ids:
            xtdata.unsubscribe_quote(seq)

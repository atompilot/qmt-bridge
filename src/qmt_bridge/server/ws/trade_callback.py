"""交易事件 WebSocket 端点 — /ws/trade。

本模块提供交易事件（委托更新、成交回报、错误通知等）的实时推送服务。

架构说明：
- BridgeTraderCallback 在 xttrader 后台线程中接收交易事件
- 通过 asyncio.run_coroutine_threadsafe 调用 broadcast_trade_event()
- broadcast_trade_event() 将事件广播给所有已连接的 WebSocket 客户端

安全机制：
- 客户端必须通过 api_key 查询参数进行身份验证
- 使用 hmac.compare_digest 进行常量时间比较，防止时序攻击
"""

import asyncio
import json
import hmac
import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

router = APIRouter()
logger = logging.getLogger("qmt_bridge.ws.trade")

# 当前已连接的交易 WebSocket 客户端集合
_trade_listeners: set[WebSocket] = set()


async def broadcast_trade_event(event: dict):
    """将交易事件广播给所有已连接的 WebSocket 客户端。

    此函数由 BridgeTraderCallback._dispatch() 通过
    asyncio.run_coroutine_threadsafe 从 xttrader 后台线程调用。

    发送失败的客户端会被自动从监听列表中移除。

    Args:
        event: 交易事件字典，包含 'type'（如 'order', 'trade', 'order_error'）
               和 'data' 字段。
    """
    dead = set()  # 记录发送失败的客户端
    for ws in _trade_listeners:
        try:
            await ws.send_json(event)
        except Exception:
            dead.add(ws)
    # 移除断开连接的客户端
    _trade_listeners.difference_update(dead)


@router.websocket("/ws/trade")
async def ws_trade(
    ws: WebSocket,
    api_key: str = Query("", alias="api_key"),
):
    """交易事件 WebSocket 端点。

    接收实时的委托/成交/错误等交易事件推送。
    需要通过查询参数 ``api_key`` 进行身份验证。

    连接示例::

        ws://localhost:8000/ws/trade?api_key=your_api_key

    推送的事件类型包括：
    - order: 委托状态更新
    - trade: 成交回报
    - order_error: 委托错误
    - cancel_error: 撤单失败
    - connected/disconnected: 交易连接状态变化
    - asset: 资产变动
    - position: 持仓变动
    - account_status: 账户状态变化

    Args:
        ws: WebSocket 连接实例。
        api_key: API 密钥，通过查询参数传递。
    """
    from ..config import get_settings

    settings = get_settings()

    # API 密钥验证
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
            # 保持连接存活，客户端可发送心跳/ping 消息
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        # 客户端断开时从监听列表中移除
        _trade_listeners.discard(ws)
        logger.info("Trade WebSocket client disconnected")

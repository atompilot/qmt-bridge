"""公式指标计算 WebSocket 端点 — /ws/formula。

本模块提供公式指标（如 MA、MACD 等技术指标）的实时订阅和计算服务。

与其他 WebSocket 端点不同，formula 端点支持在同一连接中
动态订阅/取消订阅多个公式指标，使用请求-响应模式进行交互。

使用流程：
1. 客户端建立 WebSocket 连接
2. 客户端发送订阅请求：
   {"action": "subscribe", "formula_name": "MA", "stock_code": "000001.SZ",
    "period": "1d", "count": -1, "dividend_type": "none", "params": {}}
3. 服务端返回确认：{"action": "subscribed", "seq_id": 123}
4. 公式计算结果通过回调实时推送
5. 客户端可发送取消订阅：{"action": "unsubscribe", "seq_id": 123}
6. 连接断开时自动取消所有订阅
"""

import asyncio
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()
logger = logging.getLogger("qmt_bridge.ws.formula")


@router.websocket("/ws/formula")
async def ws_formula(ws: WebSocket):
    """公式指标计算 WebSocket 端点。

    支持在单个连接中动态管理多个公式指标订阅。

    协议：
        订阅公式::

            {
                "action": "subscribe",
                "formula_name": "MA",
                "stock_code": "000001.SZ",
                "period": "1d",
                "count": -1,
                "dividend_type": "none",
                "params": {}
            }

        服务端确认::

            {"action": "subscribed", "seq_id": 123}

        公式结果推送::

            {
                "type": "formula_update",
                "formula_name": "MA",
                "stock_code": "000001.SZ",
                "data": {...}
            }

        取消订阅::

            {"action": "unsubscribe", "seq_id": 123}
    """
    await ws.accept()
    subscriptions: dict[int, bool] = {}  # 订阅序列号 → 是否活跃
    loop = asyncio.get_running_loop()

    try:
        from xtquant import xtdata

        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await ws.send_json({"error": "invalid JSON"})
                continue

            action = msg.get("action")

            if action == "subscribe":
                # 解析公式订阅参数
                formula_name = msg.get("formula_name", "")
                stock_code = msg.get("stock_code", "")
                period = msg.get("period", "1d")
                count = msg.get("count", -1)
                dividend_type = msg.get("dividend_type", "none")
                params = msg.get("params", {})

                def _callback(data, formula=formula_name, stock=stock_code):
                    """公式计算结果回调 — 在 xtdata 后台线程中被调用。

                    将计算结果序列化后通过 run_coroutine_threadsafe
                    投递到 asyncio 事件循环发送给客户端。
                    """
                    try:
                        payload = {
                            "type": "formula_update",
                            "formula_name": formula,
                            "stock_code": stock,
                            "data": _safe_serialize(data),
                        }
                        asyncio.run_coroutine_threadsafe(
                            ws.send_json(payload), loop
                        )
                    except Exception:
                        pass

                # 向 xtdata 注册公式订阅
                seq_id = xtdata.subscribe_formula(
                    formula_name, stock_code, period, count,
                    dividend_type, _callback, **params,
                )
                subscriptions[seq_id] = True
                await ws.send_json({"action": "subscribed", "seq_id": seq_id})

            elif action == "unsubscribe":
                # 取消指定的公式订阅
                seq_id = msg.get("seq_id")
                if seq_id is not None and seq_id in subscriptions:
                    xtdata.unsubscribe_formula(seq_id)
                    del subscriptions[seq_id]
                    await ws.send_json({"action": "unsubscribed", "seq_id": seq_id})
                else:
                    await ws.send_json({"error": "unknown seq_id"})

            else:
                await ws.send_json({"error": f"unknown action: {action}"})

    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("formula WS error")
    finally:
        # 清理：取消所有未取消的公式订阅
        from xtquant import xtdata as _xtd
        for seq_id in subscriptions:
            try:
                _xtd.unsubscribe_formula(seq_id)
            except Exception:
                pass


def _safe_serialize(data):
    """将 numpy/pandas 对象递归转换为原生 Python 类型，以便 JSON 序列化。

    Args:
        data: 任意数据，可能包含 numpy 数组、numpy 整数/浮点数等。

    Returns:
        转换为原生 Python 类型的数据。
    """
    import numpy as np
    if isinstance(data, dict):
        return {k: _safe_serialize(v) for k, v in data.items()}
    if isinstance(data, (list, tuple)):
        return [_safe_serialize(v) for v in data]
    if isinstance(data, np.ndarray):
        return data.tolist()
    if isinstance(data, (np.integer,)):
        return int(data)
    if isinstance(data, (np.floating,)):
        return float(data)
    return data

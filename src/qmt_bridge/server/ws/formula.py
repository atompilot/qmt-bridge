"""WebSocket — Formula subscription /ws/formula."""

import asyncio
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()
logger = logging.getLogger("qmt_bridge.ws.formula")


@router.websocket("/ws/formula")
async def ws_formula(ws: WebSocket):
    """Subscribe/unsubscribe to formula real-time updates.

    Client sends JSON messages:
      {"action": "subscribe", "formula_name": "MA", "stock_code": "000001.SZ",
       "period": "1d", "count": -1, "dividend_type": "none", "params": {}}
      {"action": "unsubscribe", "seq_id": 123}

    Server pushes formula results as they update.
    """
    await ws.accept()
    subscriptions: dict[int, bool] = {}  # seq_id → active
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
                formula_name = msg.get("formula_name", "")
                stock_code = msg.get("stock_code", "")
                period = msg.get("period", "1d")
                count = msg.get("count", -1)
                dividend_type = msg.get("dividend_type", "none")
                params = msg.get("params", {})

                def _callback(data, formula=formula_name, stock=stock_code):
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

                seq_id = xtdata.subscribe_formula(
                    formula_name, stock_code, period, count,
                    dividend_type, _callback, **params,
                )
                subscriptions[seq_id] = True
                await ws.send_json({"action": "subscribed", "seq_id": seq_id})

            elif action == "unsubscribe":
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
        from xtquant import xtdata as _xtd
        for seq_id in subscriptions:
            try:
                _xtd.unsubscribe_formula(seq_id)
            except Exception:
                pass


def _safe_serialize(data):
    """Convert numpy/pandas objects to plain Python for JSON."""
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

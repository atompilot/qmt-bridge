"""BridgeTraderCallback — bridges xttrader thread callbacks to asyncio."""

import asyncio
import logging

logger = logging.getLogger("qmt_bridge.trading.callbacks")


class BridgeTraderCallback:
    """Implements XtQuantTraderCallback interface.

    Uses ``asyncio.run_coroutine_threadsafe`` to relay events from the
    xttrader background thread into the FastAPI asyncio event loop.
    """

    def __init__(self):
        self._loop: asyncio.AbstractEventLoop | None = None
        self._notifier = None

    def set_event_loop(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop

    def set_notifier(self, notifier):
        self._notifier = notifier

    def _dispatch(self, event: dict):
        """Push an event dict to all connected trade WebSocket listeners."""
        if self._loop is None:
            return
        from ..ws.trade_callback import broadcast_trade_event
        asyncio.run_coroutine_threadsafe(broadcast_trade_event(event), self._loop)
        if self._notifier is not None:
            asyncio.run_coroutine_threadsafe(self._notifier.dispatch(event), self._loop)

    # ------------------------------------------------------------------
    # XtQuantTraderCallback interface
    # ------------------------------------------------------------------

    def on_disconnected(self):
        logger.warning("XtQuantTrader disconnected")
        self._dispatch({"type": "disconnected"})

    def on_stock_order(self, order):
        logger.debug("on_stock_order: %s", order)
        self._dispatch({
            "type": "order",
            "data": _order_to_dict(order),
        })

    def on_stock_trade(self, trade):
        logger.debug("on_stock_trade: %s", trade)
        self._dispatch({
            "type": "trade",
            "data": _trade_to_dict(trade),
        })

    def on_order_error(self, order_error):
        logger.warning("on_order_error: %s", order_error)
        self._dispatch({
            "type": "order_error",
            "data": _error_to_dict(order_error),
        })

    def on_cancel_error(self, cancel_error):
        logger.warning("on_cancel_error: %s", cancel_error)
        self._dispatch({
            "type": "cancel_error",
            "data": _error_to_dict(cancel_error),
        })

    def on_order_stock_async_response(self, response):
        logger.debug("on_order_stock_async_response: %s", response)
        self._dispatch({
            "type": "async_response",
            "data": {"order_id": getattr(response, "order_id", None)},
        })

    def on_account_status(self, status):
        logger.info("on_account_status: %s", status)
        self._dispatch({
            "type": "account_status",
            "data": {"status": str(status)},
        })

    def on_connected(self):
        logger.info("XtQuantTrader connected")
        self._dispatch({"type": "connected"})

    def on_stock_asset(self, asset):
        logger.debug("on_stock_asset: %s", asset)
        self._dispatch({
            "type": "asset",
            "data": _asset_to_dict(asset),
        })

    def on_stock_position(self, position):
        logger.debug("on_stock_position: %s", position)
        self._dispatch({
            "type": "position",
            "data": _position_to_dict(position),
        })

    def on_cancel_order_stock_async_response(self, response):
        logger.debug("on_cancel_order_stock_async_response: %s", response)
        self._dispatch({
            "type": "async_cancel_response",
            "data": {
                "order_id": getattr(response, "order_id", None),
                "cancel_result": getattr(response, "cancel_result", None),
            },
        })

    def on_smt_appointment_async_response(self, response):
        logger.debug("on_smt_appointment_async_response: %s", response)
        self._dispatch({
            "type": "smt_appointment_response",
            "data": {
                "order_id": getattr(response, "order_id", None),
                "error_id": getattr(response, "error_id", None),
                "error_msg": getattr(response, "error_msg", None),
            },
        })


def _order_to_dict(order) -> dict:
    """Convert an XtOrder object to a plain dict."""
    attrs = [
        "account_id", "stock_code", "order_id", "order_sysid",
        "order_time", "order_type", "order_volume", "price_type",
        "price", "traded_volume", "traded_price", "order_status",
        "status_msg", "strategy_name", "order_remark",
    ]
    return {a: getattr(order, a, None) for a in attrs}


def _trade_to_dict(trade) -> dict:
    """Convert an XtTrade object to a plain dict."""
    attrs = [
        "account_id", "stock_code", "order_id", "order_sysid",
        "traded_id", "traded_time", "traded_volume", "traded_price",
        "order_type", "strategy_name", "order_remark",
    ]
    return {a: getattr(trade, a, None) for a in attrs}


def _error_to_dict(error) -> dict:
    """Convert an error object to a plain dict."""
    attrs = [
        "account_id", "order_id", "error_id", "error_msg",
    ]
    return {a: getattr(error, a, None) for a in attrs}


def _asset_to_dict(asset) -> dict:
    """Convert an XtAsset object to a plain dict."""
    attrs = [
        "account_id", "cash", "frozen_cash", "market_value",
        "total_asset",
    ]
    return {a: getattr(asset, a, None) for a in attrs}


def _position_to_dict(position) -> dict:
    """Convert an XtPosition object to a plain dict."""
    attrs = [
        "account_id", "stock_code", "volume", "can_use_volume",
        "frozen_volume", "open_price", "market_value",
    ]
    return {a: getattr(position, a, None) for a in attrs}

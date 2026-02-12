"""BridgeTraderCallback — 将 xttrader 后台线程的回调桥接到 FastAPI asyncio 事件循环。

本模块实现了 XtQuantTraderCallback 接口，作为 xttrader 后台线程
与 FastAPI 主事件循环之间的桥梁：

1. xttrader 在其自有的后台线程中触发回调（如委托更新、成交通知等）
2. BridgeTraderCallback 将这些事件通过 ``asyncio.run_coroutine_threadsafe``
   安全地投递到 FastAPI 的 asyncio 事件循环中
3. 事件随后被广播到所有已连接的 WebSocket 客户端，并分发给通知后端

这种设计解决了 xttrader 回调运行在非 asyncio 线程中、
无法直接使用 ``await`` 调用异步代码的问题。
"""

import asyncio
import logging

logger = logging.getLogger("qmt_bridge.trading.callbacks")


class BridgeTraderCallback:
    """XtQuantTraderCallback 接口的实现，桥接后台线程到 asyncio。

    在整体架构中的作用：
    - 接收 xttrader 后台线程中的交易事件回调
    - 使用 ``asyncio.run_coroutine_threadsafe`` 将事件投递到主事件循环
    - 将事件广播给 WebSocket 客户端（通过 trade_callback 模块）
    - 将事件分发给通知管理器（如飞书/Webhook 通知）

    线程安全说明：
        所有 ``on_*`` 方法均在 xttrader 后台线程中被调用，
        因此不能直接 await 异步函数，必须通过
        ``asyncio.run_coroutine_threadsafe`` 将协程提交到主循环。
    """

    def __init__(self):
        """初始化回调桥接器。"""
        self._loop: asyncio.AbstractEventLoop | None = None  # FastAPI 主事件循环引用
        self._notifier = None  # NotifierManager 实例，用于分发通知

    def set_event_loop(self, loop: asyncio.AbstractEventLoop):
        """设置 asyncio 事件循环引用。

        在 FastAPI lifespan 启动阶段调用，将主事件循环传递给回调桥接器，
        以便后续通过 run_coroutine_threadsafe 投递事件。

        Args:
            loop: FastAPI 应用的 asyncio 事件循环。
        """
        self._loop = loop

    def set_notifier(self, notifier):
        """设置通知管理器。

        Args:
            notifier: NotifierManager 实例，用于将交易事件转发到飞书/Webhook 等通知渠道。
        """
        self._notifier = notifier

    def _dispatch(self, event: dict):
        """将事件从 xttrader 后台线程投递到 asyncio 事件循环。

        这是所有回调方法的核心分发逻辑：
        1. 通过 broadcast_trade_event 将事件广播给所有 WebSocket 客户端
        2. 如果配置了通知管理器，同时将事件分发给通知后端

        Args:
            event: 事件字典，包含 'type' 字段（如 'order', 'trade', 'order_error'）
                   和可选的 'data' 字段。
        """
        if self._loop is None:
            return
        # 将 WebSocket 广播协程提交到主事件循环
        from ..ws.trade_callback import broadcast_trade_event
        asyncio.run_coroutine_threadsafe(broadcast_trade_event(event), self._loop)
        # 将通知分发协程也提交到主事件循环
        if self._notifier is not None:
            asyncio.run_coroutine_threadsafe(self._notifier.dispatch(event), self._loop)

    # ------------------------------------------------------------------
    # XtQuantTraderCallback 接口实现
    # 以下所有方法均在 xttrader 后台线程中被调用
    # ------------------------------------------------------------------

    def on_disconnected(self):
        """交易连接断开回调。"""
        logger.warning("XtQuantTrader disconnected")
        self._dispatch({"type": "disconnected"})

    def on_stock_order(self, order):
        """委托状态更新回调。

        当委托状态发生变化时触发（如已报、已成、已撤等）。

        Args:
            order: XtOrder 委托对象，包含委托详情。
        """
        logger.debug("on_stock_order: %s", order)
        self._dispatch({
            "type": "order",
            "data": _order_to_dict(order),
        })

    def on_stock_trade(self, trade):
        """成交回报回调。

        当委托成交时触发。

        Args:
            trade: XtTrade 成交对象，包含成交详情。
        """
        logger.debug("on_stock_trade: %s", trade)
        self._dispatch({
            "type": "trade",
            "data": _trade_to_dict(trade),
        })

    def on_order_error(self, order_error):
        """委托错误回调。

        当下单失败时触发（如价格不合法、资金不足等）。

        Args:
            order_error: 错误对象，包含错误代码和错误消息。
        """
        logger.warning("on_order_error: %s", order_error)
        self._dispatch({
            "type": "order_error",
            "data": _error_to_dict(order_error),
        })

    def on_cancel_error(self, cancel_error):
        """撤单失败回调。

        当撤单操作失败时触发（如委托已成交无法撤销等）。

        Args:
            cancel_error: 错误对象，包含错误代码和错误消息。
        """
        logger.warning("on_cancel_error: %s", cancel_error)
        self._dispatch({
            "type": "cancel_error",
            "data": _error_to_dict(cancel_error),
        })

    def on_order_stock_async_response(self, response):
        """异步下单响应回调。

        当异步下单请求得到交易柜台响应时触发。

        Args:
            response: 响应对象，包含分配的委托编号。
        """
        logger.debug("on_order_stock_async_response: %s", response)
        self._dispatch({
            "type": "async_response",
            "data": {"order_id": getattr(response, "order_id", None)},
        })

    def on_account_status(self, status):
        """账户状态变化回调。

        当交易账户状态发生变化时触发（如登录、登出等）。

        Args:
            status: 账户状态对象。
        """
        logger.info("on_account_status: %s", status)
        self._dispatch({
            "type": "account_status",
            "data": {"status": str(status)},
        })

    def on_connected(self):
        """交易连接建立回调。"""
        logger.info("XtQuantTrader connected")
        self._dispatch({"type": "connected"})

    def on_stock_asset(self, asset):
        """账户资产变动回调。

        当账户资产信息更新时触发。

        Args:
            asset: XtAsset 资产对象，包含总资产、可用资金等。
        """
        logger.debug("on_stock_asset: %s", asset)
        self._dispatch({
            "type": "asset",
            "data": _asset_to_dict(asset),
        })

    def on_stock_position(self, position):
        """持仓变动回调。

        当持仓信息更新时触发。

        Args:
            position: XtPosition 持仓对象，包含持仓量、可用量等。
        """
        logger.debug("on_stock_position: %s", position)
        self._dispatch({
            "type": "position",
            "data": _position_to_dict(position),
        })

    def on_cancel_order_stock_async_response(self, response):
        """异步撤单响应回调。

        当异步撤单请求得到交易柜台响应时触发。

        Args:
            response: 响应对象，包含委托编号和撤单结果。
        """
        logger.debug("on_cancel_order_stock_async_response: %s", response)
        self._dispatch({
            "type": "async_cancel_response",
            "data": {
                "order_id": getattr(response, "order_id", None),
                "cancel_result": getattr(response, "cancel_result", None),
            },
        })

    def on_smt_appointment_async_response(self, response):
        """SMT 约定式交易异步响应回调。

        当 SMT 协商下单请求得到响应时触发。

        Args:
            response: 响应对象，包含委托编号、错误代码和错误消息。
        """
        logger.debug("on_smt_appointment_async_response: %s", response)
        self._dispatch({
            "type": "smt_appointment_response",
            "data": {
                "order_id": getattr(response, "order_id", None),
                "error_id": getattr(response, "error_id", None),
                "error_msg": getattr(response, "error_msg", None),
            },
        })


# ------------------------------------------------------------------
# 辅助转换函数 — 将 xtquant 对象转为可 JSON 序列化的字典
# ------------------------------------------------------------------


def _order_to_dict(order) -> dict:
    """将 XtOrder 委托对象转换为普通字典。

    Args:
        order: xtquant 返回的委托对象。

    Returns:
        包含委托关键字段的字典。
    """
    attrs = [
        "account_id", "stock_code", "order_id", "order_sysid",
        "order_time", "order_type", "order_volume", "price_type",
        "price", "traded_volume", "traded_price", "order_status",
        "status_msg", "strategy_name", "order_remark",
    ]
    return {a: getattr(order, a, None) for a in attrs}


def _trade_to_dict(trade) -> dict:
    """将 XtTrade 成交对象转换为普通字典。

    Args:
        trade: xtquant 返回的成交对象。

    Returns:
        包含成交关键字段的字典。
    """
    attrs = [
        "account_id", "stock_code", "order_id", "order_sysid",
        "traded_id", "traded_time", "traded_volume", "traded_price",
        "order_type", "strategy_name", "order_remark",
    ]
    return {a: getattr(trade, a, None) for a in attrs}


def _error_to_dict(error) -> dict:
    """将错误对象转换为普通字典。

    Args:
        error: xtquant 返回的错误对象（委托错误或撤单错误）。

    Returns:
        包含错误关键字段的字典。
    """
    attrs = [
        "account_id", "order_id", "error_id", "error_msg",
    ]
    return {a: getattr(error, a, None) for a in attrs}


def _asset_to_dict(asset) -> dict:
    """将 XtAsset 资产对象转换为普通字典。

    Args:
        asset: xtquant 返回的资产对象。

    Returns:
        包含资产关键字段的字典。
    """
    attrs = [
        "account_id", "cash", "frozen_cash", "market_value",
        "total_asset",
    ]
    return {a: getattr(asset, a, None) for a in attrs}


def _position_to_dict(position) -> dict:
    """将 XtPosition 持仓对象转换为普通字典。

    Args:
        position: xtquant 返回的持仓对象。

    Returns:
        包含持仓关键字段的字典。
    """
    attrs = [
        "account_id", "stock_code", "volume", "can_use_volume",
        "frozen_volume", "open_price", "market_value",
    ]
    return {a: getattr(position, a, None) for a in attrs}

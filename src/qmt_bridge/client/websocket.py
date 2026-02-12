"""WebSocketMixin — WebSocket 实时订阅客户端方法。

封装了通过 WebSocket 进行实时数据推送的订阅接口，包括：
- 实时行情订阅（Tick/分钟级别）
- 全市场行情订阅
- 交易事件回调订阅（委托/成交/撤单等）
- L2 千档数据订阅

需要安装 ``websockets`` 包: ``pip install websockets``

所有方法均为异步（async），需在 asyncio 事件循环中运行。
"""

import json
from typing import Callable


class WebSocketMixin:
    """WebSocket 实时订阅客户端方法集合。"""

    async def subscribe_realtime(
        self,
        stocks: list[str],
        callback: Callable[[dict], None],
        period: str = "tick",
    ):
        """订阅实时行情推送。

        通过 WebSocket 连接到服务端 ``/ws/realtime`` 端点，实时接收
        指定股票的行情更新数据。

        底层通过 ``xtdata.subscribe_quote()`` 实现实时行情订阅。

        示例::

            import asyncio
            from qmt_bridge import QMTClient

            client = QMTClient("192.168.1.100")

            def on_tick(data):
                print(f"收到行情: {data}")

            asyncio.run(client.subscribe_realtime(
                stocks=["000001.SZ", "600519.SH"],
                callback=on_tick,
            ))

        Args:
            stocks: 订阅的股票代码列表
            callback: 收到行情数据时的回调函数，参数为行情数据字典
            period: 推送周期 — ``"tick"``（逐笔）或分钟周期如 ``"1m"``
        """
        try:
            import websockets
        except ImportError:
            raise ImportError(
                "websockets package is required for realtime subscriptions. "
                "Install it with: pip install websockets"
            )

        url = f"{self.ws_url}/ws/realtime"
        async with websockets.connect(url) as ws:
            # 发送订阅请求
            await ws.send(json.dumps({"stocks": stocks, "period": period}))
            # 持续接收行情推送
            async for message in ws:
                data = json.loads(message)
                callback(data)

    async def subscribe_whole_quote(
        self,
        codes: list[str],
        callback: Callable[[dict], None],
    ):
        """订阅全市场行情推送。

        通过 WebSocket 连接到服务端 ``/ws/whole_quote`` 端点，
        接收全市场范围的行情快照数据。

        Args:
            codes: 市场代码列表
            callback: 收到数据时的回调函数
        """
        try:
            import websockets
        except ImportError:
            raise ImportError(
                "websockets package is required. Install with: pip install websockets"
            )

        url = f"{self.ws_url}/ws/whole_quote"
        async with websockets.connect(url) as ws:
            await ws.send(json.dumps({"codes": codes}))
            async for message in ws:
                data = json.loads(message)
                callback(data)

    async def subscribe_trade_events(
        self,
        callback: Callable[[dict], None],
    ):
        """订阅交易事件回调。

        通过 WebSocket 连接到服务端 ``/ws/trade`` 端点，实时接收
        交易事件推送，包括：
        - 委托回报（on_stock_order）
        - 成交回报（on_stock_trade）
        - 委托错误（on_order_error）
        - 撤单错误（on_cancel_error）
        - 账户状态变化（on_account_status）

        需要 API Key 认证。

        Args:
            callback: 收到交易事件时的回调函数
        """
        try:
            import websockets
        except ImportError:
            raise ImportError(
                "websockets package is required. Install with: pip install websockets"
            )

        # 通过 URL 查询参数传递 API Key 进行认证
        params = f"?api_key={self.api_key}" if self.api_key else ""
        url = f"{self.ws_url}/ws/trade{params}"
        async with websockets.connect(url) as ws:
            async for message in ws:
                data = json.loads(message)
                callback(data)

    async def subscribe_l2_thousand(
        self,
        stocks: list[str],
        callback: Callable[[dict], None],
    ):
        """订阅 L2 千档数据推送。

        通过 WebSocket 连接到服务端 ``/ws/l2_thousand`` 端点，
        实时接收买卖各1000档的盘口数据。

        注意: 需要开通 Level-2 行情权限。

        Args:
            stocks: 订阅的股票代码列表
            callback: 收到数据时的回调函数
        """
        try:
            import websockets
        except ImportError:
            raise ImportError(
                "websockets package is required. Install with: pip install websockets"
            )

        url = f"{self.ws_url}/ws/l2_thousand"
        async with websockets.connect(url) as ws:
            await ws.send(json.dumps({"stocks": stocks}))
            async for message in ws:
                data = json.loads(message)
                callback(data)

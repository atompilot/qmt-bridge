"""WebSocketMixin — WebSocket subscription client methods."""

import json
from typing import Callable


class WebSocketMixin:
    """Client methods for WebSocket endpoints."""

    async def subscribe_realtime(
        self,
        stocks: list[str],
        callback: Callable[[dict], None],
        period: str = "tick",
    ):
        """Subscribe to realtime quote updates via WebSocket.

        Requires the ``websockets`` package::

            pip install websockets

        Usage::

            import asyncio
            from qmt_bridge import QMTClient

            client = QMTClient("192.168.1.100")

            def on_tick(data):
                print(data)

            asyncio.run(client.subscribe_realtime(
                stocks=["000001.SZ", "600519.SH"],
                callback=on_tick,
            ))
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
            await ws.send(json.dumps({"stocks": stocks, "period": period}))
            async for message in ws:
                data = json.loads(message)
                callback(data)

    async def subscribe_whole_quote(
        self,
        codes: list[str],
        callback: Callable[[dict], None],
    ):
        """Subscribe to whole-market quote updates via WebSocket.

        Requires the ``websockets`` package.
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
        """Subscribe to trade event callbacks via WebSocket.

        Requires the ``websockets`` package and an API key.
        """
        try:
            import websockets
        except ImportError:
            raise ImportError(
                "websockets package is required. Install with: pip install websockets"
            )

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
        """Subscribe to L2 thousand-level data via WebSocket.

        Requires the ``websockets`` package.
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

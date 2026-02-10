# WebSocket 客户端

实时行情订阅、全市场行情、L2 千档、交易回报推送等 WebSocket 方法。

!!! tip "依赖"
    WebSocket 功能需要安装 `websockets` 包：`pip install "qmt-bridge[client]"`

```python
import asyncio
from qmt_bridge import QMTClient

client = QMTClient(host="192.168.1.100")

def on_tick(data):
    print(data)

asyncio.run(client.subscribe_realtime(
    stocks=["000001.SZ", "600519.SH"],
    callback=on_tick,
))
```

::: qmt_bridge.client.websocket.WebSocketMixin
    options:
      show_root_heading: false
      heading_level: 2

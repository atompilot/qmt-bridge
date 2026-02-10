# WebSocket 使用指南

QMT Bridge 提供 5 个 WebSocket 端点，用于实时数据推送。

## 端点列表

| 路径 | 说明 | 认证 |
|------|------|------|
| `/ws/realtime` | 实时行情推送 | 无 |
| `/ws/whole_quote` | 全市场行情订阅 | 无 |
| `/ws/l2_thousand` | L2 千档行情推送 | 无 |
| `/ws/download_progress` | 下载进度推送 | 无 |
| `/ws/formula` | 公式/指标实时推送 | 无 |
| `/ws/trade` | 交易回报推送 | 需要 API Key |

## 实时行情 `/ws/realtime`

连接后发送 JSON 订阅请求，服务端持续推送行情更新。

```jsonc
// 订阅请求
{ "stocks": ["000001.SZ", "600519.SH"], "period": "tick" }
```

**Python 客户端用法：**

```python
import asyncio
from qmt_bridge import QMTClient

client = QMTClient(host="192.168.1.100")

def on_tick(data):
    print(f"收到行情: {data}")

asyncio.run(client.subscribe_realtime(
    stocks=["000001.SZ", "600519.SH"],
    callback=on_tick,
))
```

## 全市场行情 `/ws/whole_quote`

订阅整个市场的行情更新。

```jsonc
// 订阅请求
{ "codes": ["SH", "SZ"] }
```

**Python 客户端用法：**

```python
asyncio.run(client.subscribe_whole_quote(
    codes=["SH", "SZ"],
    callback=on_tick,
))
```

## L2 千档行情 `/ws/l2_thousand`

订阅 L2 千档行情数据。

```jsonc
// 订阅请求
{ "stocks": ["000001.SZ"] }
```

**Python 客户端用法：**

```python
asyncio.run(client.subscribe_l2_thousand(
    stocks=["000001.SZ"],
    callback=on_tick,
))
```

## 下载进度 `/ws/download_progress`

监控数据下载进度。

```jsonc
// 订阅请求
{
    "stocks": ["000001.SZ"],
    "period": "1d",
    "start_time": "",
    "end_time": ""
}
```

下载完成后服务端发送 `{"status": "done"}`。

## 公式/指标 `/ws/formula`

实时订阅公式计算结果。

```jsonc
// 订阅
{
    "action": "subscribe",
    "formula_name": "MA",
    "stock_code": "000001.SZ",
    "period": "1d",
    "count": -1,
    "dividend_type": "none",
    "params": {}
}

// 取消订阅
{ "action": "unsubscribe", "seq_id": 123 }
```

## 交易回报 `/ws/trade`

!!! note "需要认证"
    交易回报 WebSocket 需要通过查询参数传递 API Key：`ws://<host>:8000/ws/trade?api_key=your-secret-key`

推送交易事件（委托回报、成交回报、错误信息等）。

**Python 客户端用法：**

```python
client = QMTClient(host="192.168.1.100", api_key="your-secret-key")

def on_trade_event(data):
    print(f"交易事件: {data}")

asyncio.run(client.subscribe_trade_events(callback=on_trade_event))
```

## JavaScript / 浏览器使用

```javascript
const ws = new WebSocket("ws://192.168.1.100:8000/ws/realtime");

ws.onopen = () => {
    ws.send(JSON.stringify({
        stocks: ["000001.SZ", "600519.SH"],
        period: "tick"
    }));
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log("行情更新:", data);
};
```

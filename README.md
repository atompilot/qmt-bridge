# QMT Bridge

> 将 miniQMT 的行情数据能力通过 HTTP/WebSocket 接口暴露给局域网内的任意设备，让你在 Mac/Linux 上也能自由使用 A股实时行情和历史数据。

**QMT Bridge** is a lightweight API server that wraps [xtquant](https://pypi.org/project/xtquant/) (the Python library behind miniQMT) and exposes market data as standard HTTP/WebSocket endpoints. It runs on your Windows machine alongside the QMT client, allowing any device on your local network — Mac, Linux, or mobile — to access real-time quotes, historical K-lines, sector data, and more.

## Why

miniQMT / xtquant 只能在 Windows 上运行，且必须依赖 QMT 客户端保持登录。如果你的主力开发机是 Mac 或 Linux，就无法直接调用 xtquant。

QMT Bridge 解决这个问题：Windows 电脑作为数据中转站，运行 QMT 客户端 + 本项目的 API 服务；你的 Mac/Linux 通过局域网 HTTP 请求获取所有数据，核心代码、数据库、分析逻辑全部在你自己的主力机上运行。

```
Mac / Linux (主力机)                    Windows (中转站)
┌──────────────────────┐                ┌─────────────────────────┐
│  你的分析代码          │   HTTP/WS     │  miniQMT 客户端 (登录中)  │
│  本地数据库            │ ◄───────────► │  QMT Bridge (FastAPI)    │
│  可视化仪表盘          │   局域网       │                         │
└──────────────────────┘                └─────────────────────────┘
```

## Features

- **REST API** — 历史 K 线、批量查询、板块成分股、股票详情、最新 tick 快照
- **WebSocket** — 实时行情推送，支持 tick 和分钟级别订阅
- **零业务逻辑** — 纯数据管道，不含任何交易策略代码
- **不涉及自动交易** — 仅暴露行情数据接口，不包含下单功能

## Prerequisites

### Windows 端

- **Python** 3.8+ (推荐 3.10 或 3.11)
- **QMT 客户端** — 已安装并获得券商账号密码（需联系客户经理开通）
- **xtquant** — `pip install xtquant`

### 网络

- Windows 和你的主力机在同一局域网下（连同一个路由器 / WiFi）
- Windows 防火墙放行本项目使用的端口（默认 8000）

## Quick Start

### 1. 安装依赖

```bash
git clone https://github.com/yourname/qmt-bridge.git
cd qmt-bridge
pip install -r requirements.txt
```

### 2. 启动 QMT 客户端

打开 QMT，勾选 **"独立交易"** 模式登录，保持窗口运行（可最小化）。

### 3. 启动 API 服务

```bash
python server.py
```

默认监听 `0.0.0.0:8000`，可通过参数修改：

```bash
python server.py --host 0.0.0.0 --port 8080
```

### 4. 验证

在你的 Mac/Linux 浏览器中访问：

```
http://<Windows局域网IP>:8000/docs
```

看到 FastAPI 自动生成的 Swagger 文档页面即表示服务正常运行。

## API Reference

### REST Endpoints

| Method | Path | Description | Parameters |
|--------|------|-------------|------------|
| GET | `/api/history` | 获取单只股票历史 K 线 | `stock`, `period`, `count`, `fields` |
| GET | `/api/batch_history` | 批量获取多只股票历史数据 | `stocks`, `period`, `count`, `fields` |
| GET | `/api/full_tick` | 获取最新 tick 快照 | `stocks` |
| GET | `/api/sector_stocks` | 获取板块成分股列表 | `sector` |
| GET | `/api/instrument_detail` | 获取股票基本信息 | `stock` |
| POST | `/api/download` | 触发历史数据下载到 QMT 本地缓存 | `stock`, `period`, `start`, `end` |

### WebSocket

| Path | Description |
|------|-------------|
| `ws://<host>:<port>/ws/realtime` | 实时行情推送 |

连接后发送 JSON 订阅请求：

```json
{
  "stocks": ["000001.SZ", "600519.SH"],
  "period": "tick"
}
```

### Examples

```bash
# 获取平安银行最近 60 根日线
curl "http://192.168.1.100:8000/api/history?stock=000001.SZ&period=1d&count=60"

# 批量获取多只股票 5 分钟线
curl "http://192.168.1.100:8000/api/batch_history?stocks=000001.SZ,600519.SH&period=5m&count=100"

# 获取沪深 A 股成分股列表
curl "http://192.168.1.100:8000/api/sector_stocks?sector=沪深A股"
```

## Python Client

项目附带一个轻量客户端类，可直接在 Mac/Linux 端使用：

```python
from qmt_client import QMTClient

client = QMTClient(host="192.168.1.100")

# 获取历史 K 线，返回 pandas DataFrame
df = client.get_history("000001.SZ", period="1d", count=60)
print(df)

# 获取板块成分股
stocks = client.get_sector_stocks("沪深A股")

# 实时行情订阅
import asyncio

def on_tick(data):
    print(data)

asyncio.run(client.subscribe_realtime(
    stocks=["000001.SZ", "600519.SH"],
    callback=on_tick
))
```

## Project Structure

```
qmt-bridge/
├── server.py          # FastAPI 服务主文件
├── qmt_client.py      # Python 客户端类（供远程机器使用）
├── requirements.txt   # Python 依赖
└── README.md
```

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `QMT_BRIDGE_HOST` | `0.0.0.0` | 监听地址 |
| `QMT_BRIDGE_PORT` | `8000` | 监听端口 |

也可通过命令行参数 `--host` / `--port` 指定。

## FAQ

**Q: QMT 客户端必须一直开着吗？**

是的。xtquant 通过 QMT 客户端获取行情数据，客户端关闭后 API 服务将无法返回实时数据。历史数据如果已经下载到本地缓存，在脱机模式下仍可访问。

**Q: 支持自动下单吗？**

不支持，也不计划支持。本项目仅暴露行情数据接口，所有交易决策和执行应由使用者手动完成。

**Q: 非交易时间能用吗？**

可以。历史 K 线数据、板块成分股等静态数据在非交易时间也能正常获取。实时 tick 在非交易时间没有数据推送。

**Q: 数据延迟大吗？**

局域网内 HTTP 请求延迟通常在 1-5ms，对于辅助决策的场景完全够用。实时 tick 通过 WebSocket 推送，延迟取决于 QMT 客户端本身的行情速度。

**Q: 可以在公网环境下使用吗？**

技术上可以（通过端口映射或内网穿透），但**强烈不建议**。本项目没有做认证鉴权，暴露到公网意味着任何人都能访问你的行情数据接口。如果确有需要，请自行添加 API Key 或 Token 认证。

## Security Notice

本项目设计为**仅在可信局域网内使用**，默认不包含任何身份认证机制。请勿将服务直接暴露到公网。

## License

MIT
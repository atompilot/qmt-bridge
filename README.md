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

- **REST API** — 历史 K 线、批量查询、板块成分股、股票详情、最新 tick 快照、财务数据、指数权重、期权/可转债/ETF 数据、期货主力合约等
- **WebSocket** — 实时行情推送、整市场行情订阅、下载进度推送
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

### Legacy Endpoints (backward compatible)

| Method | Path | Description | Parameters |
|--------|------|-------------|------------|
| GET | `/api/history` | 获取单只股票历史 K 线 | `stock`, `period`, `count`, `fields` |
| GET | `/api/batch_history` | 批量获取多只股票历史数据 | `stocks`, `period`, `count`, `fields` |
| GET | `/api/full_tick` | 获取最新 tick 快照 | `stocks` |
| GET | `/api/sector_stocks` | 获取板块成分股列表 | `sector` |
| GET | `/api/instrument_detail` | 获取股票基本信息 | `stock` |
| POST | `/api/download` | 触发历史数据下载到 QMT 本地缓存 | `stock`, `period`, `start`, `end` |

### Market — 行情数据 `/api/market/*`

| Method | Path | Description | Parameters |
|--------|------|-------------|------------|
| GET | `/api/market/snapshot` | 实时行情快照（大盘/个股通用） | `stocks` |
| GET | `/api/market/indices` | 主要指数行情概览（一键大盘全景） | — |
| GET | `/api/market/history_ex` | 增强版 K 线（支持除权、填充） | `stocks`, `period`, `start_time`, `end_time`, `count`, `dividend_type`, `fill_data` |
| GET | `/api/market/local_data` | 仅读本地缓存（离线可用） | `stocks`, `period`, `start_time`, `end_time`, `count`, `dividend_type`, `fill_data` |
| GET | `/api/market/divid_factors` | 除权因子 | `stock`, `start_time`, `end_time` |

### Tick & L2 — 逐笔数据 `/api/tick/*`

| Method | Path | Description | Parameters |
|--------|------|-------------|------------|
| GET | `/api/tick/l2_quote` | L2 行情快照 | `stock`, `start_time`, `end_time`, `count` |
| GET | `/api/tick/l2_order` | L2 逐笔委托 | `stock`, `start_time`, `end_time`, `count` |
| GET | `/api/tick/l2_transaction` | L2 逐笔成交 | `stock`, `start_time`, `end_time`, `count` |

### Sector — 板块数据 `/api/sector/*`

| Method | Path | Description | Parameters |
|--------|------|-------------|------------|
| GET | `/api/sector/list` | 获取所有板块列表 | — |
| GET | `/api/sector/stocks` | 获取板块成分股列表 | `sector`, `real_timetag` |
| GET | `/api/sector/info` | 板块元数据 | `sector` |

### Calendar — 交易日历 `/api/calendar/*`

| Method | Path | Description | Parameters |
|--------|------|-------------|------------|
| GET | `/api/calendar/trading_dates` | 交易日列表 | `market`, `start_time`, `end_time`, `count` |
| GET | `/api/calendar/holidays` | 节假日列表 | — |
| GET | `/api/calendar/trading_calendar` | 含未来日期的完整日历 | `market`, `start_time`, `end_time` |
| GET | `/api/calendar/trading_period` | 交易时段 | `stock` |

### Financial — 财务数据 `/api/financial/*`

| Method | Path | Description | Parameters |
|--------|------|-------------|------------|
| GET | `/api/financial/data` | 财务报表数据 | `stocks`, `tables`, `start_time`, `end_time`, `report_type` |

### Instrument — 合约信息 `/api/instrument/*`

| Method | Path | Description | Parameters |
|--------|------|-------------|------------|
| GET | `/api/instrument/batch_detail` | 批量合约详情 | `stocks`, `iscomplete` |
| GET | `/api/instrument/type` | 判断代码类型 | `stock` |
| GET | `/api/instrument/ipo_info` | IPO 信息 | `start_time`, `end_time` |
| GET | `/api/instrument/index_weight` | 指数成分股权重 | `index_code` |
| GET | `/api/instrument/st_history` | ST 历史 | `stock` |

### Option — 期权数据 `/api/option/*`

| Method | Path | Description | Parameters |
|--------|------|-------------|------------|
| GET | `/api/option/detail` | 期权合约详情 | `option_code` |
| GET | `/api/option/chain` | 标的对应的期权链 | `undl_code` |
| GET | `/api/option/list` | 按到期日/类型筛选期权 | `undl_code`, `dedate`, `opttype`, `isavailable` |
| GET | `/api/option/history_list` | 历史期权列表 | `undl_code`, `dedate` |

### ETF & Convertible Bond — `/api/etf/*` & `/api/cb/*`

| Method | Path | Description | Parameters |
|--------|------|-------------|------------|
| GET | `/api/etf/list` | ETF 代码列表（轻量） | — |
| GET | `/api/etf/info` | ETF 申赎清单 | — |
| GET | `/api/cb/info` | 可转债信息 | `stock` |

### Futures — 期货数据 `/api/futures/*`

| Method | Path | Description | Parameters |
|--------|------|-------------|------------|
| GET | `/api/futures/main_contract` | 期货主力合约 | `code_market`, `start_time`, `end_time` |
| GET | `/api/futures/sec_main_contract` | 期货次主力合约 | `code_market`, `start_time`, `end_time` |

### Meta — 系统元数据 `/api/meta/*`

| Method | Path | Description | Parameters |
|--------|------|-------------|------------|
| GET | `/api/meta/markets` | 可用市场列表 | — |
| GET | `/api/meta/periods` | 可用 K 线周期列表 | — |
| GET | `/api/meta/stock_list` | 按类别获取证券代码列表 | `category` |
| GET | `/api/meta/last_trade_date` | 最近交易日 | `market` |

### Download — 数据下载 `/api/download/*`

| Method | Path | Description | Parameters |
|--------|------|-------------|------------|
| POST | `/api/download/batch` | 批量下载历史数据 | `stocks`, `period`, `start_time`, `end_time` |
| POST | `/api/download/financial` | 下载财务数据 | `stocks`, `tables`, `start_time`, `end_time` |
| POST | `/api/download/sector_data` | 下载板块数据 | — |
| POST | `/api/download/index_weight` | 下载指数权重 | — |
| POST | `/api/download/etf_info` | 下载 ETF 信息 | — |
| POST | `/api/download/cb_data` | 下载可转债数据 | — |
| POST | `/api/download/history_contracts` | 下载过期合约 | — |

### WebSocket

| Path | Description |
|------|-------------|
| `ws://<host>:<port>/ws/realtime` | 实时行情推送 |
| `ws://<host>:<port>/ws/whole_quote` | 整市场行情订阅推送 |
| `ws://<host>:<port>/ws/download_progress` | 下载进度推送 |

**`/ws/realtime`** — 连接后发送 JSON 订阅请求：

```json
{
  "stocks": ["000001.SZ", "600519.SH"],
  "period": "tick"
}
```

**`/ws/whole_quote`** — 连接后发送市场/股票列表：

```json
{
  "codes": ["SH", "SZ"]
}
```

**`/ws/download_progress`** — 连接后发送下载任务参数：

```json
{
  "stocks": ["000001.SZ"],
  "period": "1d",
  "start_time": "",
  "end_time": ""
}
```

### Examples

```bash
# 获取平安银行最近 60 根日线（legacy）
curl "http://192.168.1.100:8000/api/history?stock=000001.SZ&period=1d&count=60"

# 增强版 K 线，前复权
curl "http://192.168.1.100:8000/api/market/history_ex?stocks=000001.SZ&period=1d&count=5&dividend_type=front"

# 获取所有可用市场
curl "http://192.168.1.100:8000/api/meta/markets"

# 获取可用 K 线周期
curl "http://192.168.1.100:8000/api/meta/periods"

# 获取所有板块列表
curl "http://192.168.1.100:8000/api/sector/list"

# 获取沪深 A 股成分股列表（legacy）
curl "http://192.168.1.100:8000/api/sector_stocks?sector=沪深A股"

# 获取沪深 A 股成分股列表（新端点）
curl "http://192.168.1.100:8000/api/sector/stocks?sector=沪深A股"

# 大盘行情一览
curl "http://192.168.1.100:8000/api/market/indices"

# 个股/指数快照
curl "http://192.168.1.100:8000/api/market/snapshot?stocks=000001.SH,000001.SZ"

# ETF 代码列表
curl "http://192.168.1.100:8000/api/etf/list"

# 按类别获取证券列表
curl "http://192.168.1.100:8000/api/meta/stock_list?category=沪深指数"

# 最近交易日
curl "http://192.168.1.100:8000/api/meta/last_trade_date?market=SH"

# 获取交易日列表
curl "http://192.168.1.100:8000/api/calendar/trading_dates?market=SH"

# 获取节假日列表
curl "http://192.168.1.100:8000/api/calendar/holidays"

# 获取指数成分股权重
curl "http://192.168.1.100:8000/api/instrument/index_weight?index_code=000300.SH"

# 获取财务数据
curl "http://192.168.1.100:8000/api/financial/data?stocks=000001.SZ&tables=Balance"

# 批量下载历史数据
curl -X POST "http://192.168.1.100:8000/api/download/batch" \
  -H "Content-Type: application/json" \
  -d '{"stocks": ["000001.SZ", "600519.SH"], "period": "1d"}'
```

## Python Client

项目附带一个轻量客户端类，可直接在 Mac/Linux 端使用：

```python
from qmt_client import QMTClient

client = QMTClient(host="192.168.1.100")

# 获取历史 K 线，返回 pandas DataFrame
df = client.get_history("000001.SZ", period="1d", count=60)
print(df)

# 增强版 K 线，前复权
dfs = client.get_history_ex(["000001.SZ"], dividend_type="front", count=60)

# 获取板块列表
sectors = client.get_sector_list()

# 获取板块成分股
stocks = client.get_sector_stocks("沪深A股")

# 大盘行情一览
indices = client.get_major_indices()

# 个股快照
snapshot = client.get_market_snapshot(["000001.SZ", "600519.SH"])

# ETF 代码列表
etfs = client.get_etf_list()

# 按类别获取证券列表
all_indices = client.get_stock_list_by_category("沪深指数")

# 最近交易日
last_date = client.get_last_trade_date("SH")

# 获取交易日列表
dates = client.get_trading_dates("SH")

# 获取财务数据
fin = client.get_financial_data(["000001.SZ"], tables=["Balance"])

# 获取可用市场
markets = client.get_markets()

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
├── server.py              # FastAPI app, .env 加载, 路由注册, uvicorn 入口
├── helpers.py             # 数据转换工具函数
├── models.py              # Pydantic 请求模型
├── routers/
│   ├── __init__.py
│   ├── market.py          # 行情数据 /api/market/*
│   ├── tick.py            # Tick & L2 /api/tick/*
│   ├── sector.py          # 板块 /api/sector/*
│   ├── calendar.py        # 交易日历 /api/calendar/*
│   ├── financial.py       # 财务数据 /api/financial/*
│   ├── instrument.py      # 合约信息 /api/instrument/*
│   ├── option.py          # 期权 /api/option/*
│   ├── etf.py             # ETF & 可转债 /api/etf/*, /api/cb/*
│   ├── futures.py         # 期货 /api/futures/*
│   ├── meta.py            # 系统元数据 /api/meta/*
│   └── download.py        # 数据下载 /api/download/*
├── qmt_client.py          # Python 客户端类（供远程机器使用）
├── requirements.txt       # Python 依赖
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

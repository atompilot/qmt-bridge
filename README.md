# QMT Bridge

> 将 miniQMT 的行情与交易能力通过 HTTP/WebSocket 接口暴露给局域网内的任意设备，让你在 Mac/Linux 上也能自由使用 A 股实时行情、历史数据和程序化交易。

**QMT Bridge** is a lightweight API server that wraps [xtquant](https://dict.thinktrader.net/nativeApi/start_now.html) (the Python library behind miniQMT) and exposes market data & trading as standard HTTP/WebSocket endpoints. It runs on your Windows machine alongside the QMT client, allowing any device on your local network — Mac, Linux, or mobile — to access real-time quotes, historical K-lines, sector data, trading, and more.

```
Mac / Linux (主力机)                    Windows (中转站)
┌──────────────────────┐                ┌─────────────────────────┐
│  你的分析 / 交易代码    │   HTTP/WS     │  miniQMT 客户端 (登录中)  │
│  本地数据库            │ ◄───────────► │  QMT Bridge (FastAPI)    │
│  可视化仪表盘          │   局域网       │  xtquant                 │
└──────────────────────┘                └─────────────────────────┘
```

## Why

miniQMT / xtquant 只能在 Windows 上运行，且必须依赖 QMT 客户端保持登录。如果你的主力开发机是 Mac 或 Linux，就无法直接调用 xtquant。

QMT Bridge 解决这个问题：Windows 电脑作为数据中转站，运行 QMT 客户端 + 本项目的 API 服务；你的 Mac/Linux 通过局域网 HTTP/WebSocket 请求获取所有数据，也可以远程下单。核心代码、数据库、分析逻辑全部在你自己的主力机上运行。

## Features

- **100+ REST API 端点** — 历史 K 线、实时行情、L2 逐笔、板块管理、财务数据、指数权重、期权链、可转债、ETF、港股通、期货主力合约等
- **5 个 WebSocket 端点** — 实时行情推送、全市场行情、L2 千档、下载进度、交易回报
- **程序化交易** (可选) — 下单、撤单、批量委托、融资融券、银证转账、智能交易
- **零依赖客户端** — Python 客户端基于 stdlib，无需安装 xtquant 即可在任意平台使用
- **API Key 认证** — 可选的 API Key 保护，交易端点强制认证
- **自动预下载** — 服务启动时自动下载板块、日历、指数权重等基础数据，之后每日定时刷新，客户端无需手动触发

## Prerequisites

### Windows 端 (服务端)

- **Python** 3.10+
- **QMT 客户端** — 已安装并获得券商账号密码（需联系客户经理开通 miniQMT 权限）
- **xtquant** — 通常随 QMT 客户端安装，或 `pip install xtquant`

### 网络

- Windows 和你的主力机在同一局域网下（连同一个路由器 / WiFi）
- Windows 防火墙放行本项目使用的端口（默认 8000）

## Quick Start

### 1. 安装

```bash
git clone https://github.com/qmt-bridge/qmt-bridge.git
cd qmt-bridge

# 安装服务端（含 WebSocket 支持）
pip install -e ".[full]"

# 或者只安装服务端（不含 WebSocket）
pip install -e ".[server]"
```

如果只需要在远程机器上使用客户端：

```bash
# 零依赖安装（仅 HTTP）
pip install -e .

# 含 WebSocket 订阅支持
pip install -e ".[client]"
```

### 2. 配置

```bash
cp .env.example .env
# 按需编辑 .env
```

### 3. 启动 QMT 客户端

打开 QMT，勾选 **"独立交易"** 模式登录，保持窗口运行（可最小化）。

### 4. 启动 API 服务

```bash
# 使用 CLI 命令（推荐）
qmt-server

# 自定义参数
qmt-server --port 8080 --log-level debug

# 启用交易模块
qmt-server --trading --api-key your-secret-key --mini-qmt-path "C:\国金QMT交易端\userdata_mini" --account-id 12345678
```

也可以使用脚本：

```bash
# 前台运行（Ctrl+C 停止）
bash scripts/start.sh

# 后台运行
bash scripts/start-nohup.sh
bash scripts/stop.sh

# Windows
scripts\start.bat
scripts\stop.bat
```

### 5. 验证

在你的 Mac/Linux 浏览器中访问：

```
http://<Windows局域网IP>:8000/docs
```

看到 Swagger 文档页面即表示服务正常。也可以用 curl 检查：

```bash
curl http://<Windows局域网IP>:8000/api/meta/health
```

## Configuration

通过 `.env` 文件或环境变量配置，CLI 参数优先级最高。

| 环境变量 | CLI 参数 | 默认值 | 说明 |
|---------|---------|-------|------|
| `QMT_BRIDGE_HOST` | `--host` | `0.0.0.0` | 监听地址（`0.0.0.0` = 允许局域网访问） |
| `QMT_BRIDGE_PORT` | `--port` | `8000` | 监听端口 |
| `QMT_BRIDGE_LOG_LEVEL` | `--log-level` | `info` | 日志级别：critical / error / warning / info / debug |
| `QMT_BRIDGE_WORKERS` | `--workers` | `1` | Worker 数量（Windows 下建议保持 1） |
| `QMT_BRIDGE_API_KEY` | `--api-key` | _(空)_ | API Key，用于保护交易端点 |
| `QMT_BRIDGE_REQUIRE_AUTH_FOR_DATA` | — | `false` | 数据端点是否也要求认证 |
| `QMT_BRIDGE_TRADING_ENABLED` | `--trading` | `false` | 是否启用交易模块 |
| `QMT_BRIDGE_MINI_QMT_PATH` | `--mini-qmt-path` | _(空)_ | miniQMT 安装路径（交易模块需要） |
| `QMT_BRIDGE_TRADING_ACCOUNT_ID` | `--account-id` | _(空)_ | 交易账户 ID |

## Auto Pre-download（自动预下载）

服务端启动时会自动在后台执行一轮基础数据预下载，之后每 24 小时自动刷新。客户端无需手动调用 `/api/download/*` 即可直接查询板块、日历、指数权重等数据。

| 下载项 | 说明 |
|-------|------|
| `download_sector_data` | 板块分类与成分股 |
| `download_holiday_data` | 节假日日历 |
| `download_history_contracts` | 期货/期权过期合约映射 |
| `download_index_weight` | 指数成分权重 |
| `download_etf_info` | ETF 申赎清单 |
| `download_cb_data` | 可转债数据 |

以下接口 **不纳入** 自动调度，仍需客户端按需调用：

- `download_history_data2` — 需要具体股票代码与时间范围
- `download_financial_data2` — 需要股票代码，且耗时较长
- `download_metatable_data` — 合约元数据表，按需获取即可

调度基于 `asyncio` 后台协程实现，无第三方依赖。预下载日志可在服务端输出中查看（关键字：`预下载完成` / `预下载失败`）。

## API Reference

完整 API 文档请访问运行中的服务 `/docs`（Swagger UI）或 `/redoc`（ReDoc）。以下为端点概览。

### Legacy Endpoints（向后兼容）

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/history` | 单只股票历史 K 线 |
| GET | `/api/batch_history` | 批量获取多只股票历史数据 |
| GET | `/api/full_tick` | 最新 tick 快照 |
| GET | `/api/sector_stocks` | 板块成分股列表 |
| GET | `/api/instrument_detail` | 股票基本信息 |
| POST | `/api/download` | 触发历史数据下载 |

### Market — 行情数据 `/api/market/*`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/market/full_tick` | 实时行情快照（个股 / 指数） |
| GET | `/api/market/indices` | 主要指数行情概览 |
| GET | `/api/market/market_data_ex` | 增强版 K 线（除权、填充） |
| GET | `/api/market/local_data` | 仅读本地缓存（离线可用） |
| GET | `/api/market/divid_factors` | 除权因子 |
| GET | `/api/market/market_data` | 通用行情数据查询 |

### Tick & L2 — 逐笔数据 `/api/tick/*`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/tick/l2_quote` | L2 行情快照 |
| GET | `/api/tick/l2_order` | L2 逐笔委托 |
| GET | `/api/tick/l2_transaction` | L2 逐笔成交 |
| GET | `/api/tick/l2_thousand_quote` | L2 千档行情 |

### Sector — 板块数据 `/api/sector/*`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/sector/list` | 所有板块列表 |
| GET | `/api/sector/stocks` | 板块成分股（支持历史日期） |
| GET | `/api/sector/info` | 板块元数据 |
| POST | `/api/sector/create_folder` | 创建板块文件夹 |
| POST | `/api/sector/create` | 创建自定义板块 |
| POST | `/api/sector/add_stocks` | 添加成分股 |
| POST | `/api/sector/remove_stocks` | 移除成分股 |
| DELETE | `/api/sector/remove` | 删除板块 |

### Calendar — 交易日历 `/api/calendar/*`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/calendar/trading_dates` | 交易日列表 |
| GET | `/api/calendar/holidays` | 节假日列表 |
| GET | `/api/calendar/trading_calendar` | 完整日历 |
| GET | `/api/calendar/trading_period` | 交易时段 |
| GET | `/api/calendar/is_trading_date` | 日期校验 |
| GET | `/api/calendar/prev_trading_date` | 上一个交易日 |
| GET | `/api/calendar/next_trading_date` | 下一个交易日 |

### Financial — 财务数据 `/api/financial/*`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/financial/data` | 财务报表数据（资产负债表 / 利润表等） |

### Instrument — 合约信息 `/api/instrument/*`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/instrument/detail_list` | 批量合约详情 |
| GET | `/api/instrument/type` | 代码类型判断 |
| GET | `/api/instrument/ipo_info` | IPO 信息 |
| GET | `/api/instrument/index_weight` | 指数成分股权重 |
| GET | `/api/instrument/his_st_data` | ST 历史 |

### Option — 期权数据 `/api/option/*`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/option/detail` | 期权合约详情 |
| GET | `/api/option/chain` | 标的期权链 |
| GET | `/api/option/list` | 按到期日 / 类型筛选 |
| GET | `/api/option/his_option_list` | 历史期权列表 |

### ETF & Convertible Bond — `/api/etf/*` & `/api/cb/*`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/etf/list` | ETF 代码列表 |
| GET | `/api/etf/info` | ETF 申赎清单 |
| GET | `/api/cb/list` | 可转债列表 |
| GET | `/api/cb/info` | 可转债信息 |

### Futures — 期货数据 `/api/futures/*`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/futures/main_contract` | 主力合约 |
| GET | `/api/futures/sec_main_contract` | 次主力合约 |

### HK — 港股通 `/api/hk/*`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/hk/stock_list` | 港股通标的列表 |
| GET | `/api/hk/connect_stocks` | 按方向筛选（沪港通 / 深港通） |

### Meta — 系统元数据 `/api/meta/*`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/meta/health` | 健康检查 |
| GET | `/api/meta/version` | 服务版本 |
| GET | `/api/meta/xtdata_version` | xtquant 版本 |
| GET | `/api/meta/connection_status` | xtdata 连接状态 |
| GET | `/api/meta/markets` | 可用市场列表 |
| GET | `/api/meta/period_list` | K 线周期列表 |
| GET | `/api/meta/stock_list` | 按类别获取证券列表 |
| GET | `/api/meta/last_trade_date` | 最近交易日 |

### Download — 数据下载 `/api/download/*`

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/download/history_data2` | 批量下载历史数据 |
| POST | `/api/download/financial_data` | 下载财务数据 |
| POST | `/api/download/sector_data` | 下载板块数据 |
| POST | `/api/download/index_weight` | 下载指数权重 |
| POST | `/api/download/etf_info` | 下载 ETF 信息 |
| POST | `/api/download/cb_data` | 下载可转债数据 |
| POST | `/api/download/history_contracts` | 下载过期合约 |

### Trading — 交易 `/api/trading/*` (需要 API Key)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/trading/order` | 下单 |
| POST | `/api/trading/cancel` | 撤单 |
| POST | `/api/trading/batch_order` | 批量下单 |
| GET | `/api/trading/orders` | 查询委托 |
| GET | `/api/trading/trades` | 查询成交 |
| GET | `/api/trading/positions` | 查询持仓 |
| GET | `/api/trading/asset` | 查询资产 |
| GET | `/api/trading/order_detail` | 查询单笔委托 |

### Credit — 融资融券 `/api/credit/*` (需要 API Key)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/credit/order` | 信用交易下单 |
| GET | `/api/credit/quota` | 额度查询 |
| GET | `/api/credit/position` | 信用持仓 |

### Fund & Bank — 资金划转 (需要 API Key)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/fund/transfer` | 资金划转 |
| GET | `/api/fund/history` | 划转记录 |
| POST | `/api/bank/transfer` | 银证转账 |

### WebSocket

| Path | Description |
|------|-------------|
| `/ws/realtime` | 实时行情推送 |
| `/ws/whole_quote` | 全市场行情订阅 |
| `/ws/l2_thousand` | L2 千档行情推送 |
| `/ws/download_progress` | 下载进度推送 |
| `/ws/trade` | 交易回报推送 (需要 API Key) |

WebSocket 连接后发送 JSON 订阅请求：

```jsonc
// /ws/realtime
{ "stocks": ["000001.SZ", "600519.SH"], "period": "tick" }

// /ws/whole_quote
{ "codes": ["SH", "SZ"] }

// /ws/l2_thousand
{ "stocks": ["000001.SZ"] }

// /ws/download_progress
{ "stocks": ["000001.SZ"], "period": "1d", "start_time": "", "end_time": "" }
```

## Realtime K-line（实时 K 线）

构建盘中实时 K 线的标准模式：**REST 拉历史 + WebSocket 推增量**。

```
            初始化                                持续更新
┌──────────────────────────┐     ┌──────────────────────────────────┐
│ GET /api/market/          │     │ WS  /ws/realtime                 │
│     market_data_ex        │     │     {"stocks":["000001.SZ"],     │
│   period=1m, count=240    │     │      "period":"1m"}              │
│                           │     │                                  │
│   ← 返回 240 根已完结 K 线  │     │   ← 持续推送最新 1m K 线柱        │
└────────────┬─────────────┘     └──────────────┬───────────────────┘
             │                                  │
             ▼                                  ▼
      ┌─────────────────────────────────────────────────┐
      │  客户端本地 K 线数组                               │
      │  - 初始化：填充历史数据                             │
      │  - 推送到来时：                                    │
      │    · 时间戳 == 最后一根 → 更新（盘中未完结柱）        │
      │    · 时间戳 > 最后一根  → 追加（新柱）               │
      └─────────────────────────────────────────────────┘
```

**步骤：**

1. **拉取历史** — 调用 REST 接口获取已完结的历史 K 线填充图表
2. **订阅实时** — 连接 WebSocket，订阅相同周期（如 `1m`）
3. **客户端合并** — WebSocket 推送的是 xtdata 聚合好的 K 线柱（非原始 tick），按时间戳判断是更新最后一根还是追加新柱

> **注意：** `subscribe_quote(period="1m")` 推送的已经是聚合好的分钟 K 线，无需客户端自行从 tick 合成。支持的周期：`tick`、`1m`、`5m`、`15m`、`30m`、`60m`、`1d`。

**Python 客户端示例：**

```python
import asyncio
from qmt_bridge import QMTClient

client = QMTClient(host="192.168.1.100")

# 1. 拉取历史 K 线
history = client.get_history_ex(["000001.SZ"], period="1m", count=240)

# 2. WebSocket 订阅实时更新
def on_kline(data):
    # data 是 xtdata 聚合好的 K 线柱
    # 按时间戳与本地数组最后一根比较：相同则更新，更大则追加
    print(data)

asyncio.run(client.subscribe_realtime(
    stocks=["000001.SZ"],
    period="1m",       # 订阅 1 分钟 K 线（非 tick）
    callback=on_kline,
))
```

## Python Client

项目附带零依赖 Python 客户端，可在任意平台使用（无需安装 xtquant）。

### 基本用法

```python
from qmt_bridge import QMTClient

client = QMTClient(host="192.168.1.100", port=8000)

# 历史 K 线
df = client.get_history("000001.SZ", period="1d", count=60)

# 增强版 K 线，前复权
dfs = client.get_history_ex(["000001.SZ", "600519.SH"], dividend_type="front", count=60)

# 大盘行情一览
indices = client.get_major_indices()

# 实时快照
snapshot = client.get_market_snapshot(["000001.SZ", "600519.SH"])

# 板块
sectors = client.get_sector_list()
stocks = client.get_sector_stocks("沪深A股")

# 财务数据
fin = client.get_financial_data(["000001.SZ"], tables=["Balance"])

# ETF / 期权 / 期货
etfs = client.get_etf_list()
options = client.get_option_list("000300.SH", "20250321")
main_contract = client.get_main_contract("IF.CFE")

# 元数据
markets = client.get_markets()
periods = client.get_periods()
last_date = client.get_last_trade_date("SH")
```

### 交易 (需要 API Key)

```python
client = QMTClient(host="192.168.1.100", api_key="your-secret-key")

# 下单
order_id = client.place_order(
    stock_code="000001.SZ",
    order_type=23,        # 买入
    order_volume=100,
    price_type=5,         # 最新价
)

# 查询
orders = client.query_orders()
positions = client.query_positions()
asset = client.query_asset()

# 撤单
client.cancel_order(order_id)
```

### WebSocket 实时订阅

```python
import asyncio

def on_tick(data):
    print(data)

# 实时行情
asyncio.run(client.subscribe_realtime(
    stocks=["000001.SZ", "600519.SH"],
    callback=on_tick,
))

# 全市场行情
asyncio.run(client.subscribe_whole_quote(
    codes=["SH", "SZ"],
    callback=on_tick,
))
```

## Examples

```bash
# 健康检查
curl http://192.168.1.100:8000/api/meta/health

# 平安银行最近 60 根日线
curl "http://192.168.1.100:8000/api/history?stock=000001.SZ&period=1d&count=60"

# 增强版 K 线，前复权
curl "http://192.168.1.100:8000/api/market/market_data_ex?stocks=000001.SZ&period=1d&count=5&dividend_type=front"

# 大盘行情
curl http://192.168.1.100:8000/api/market/indices

# 个股 / 指数快照
curl "http://192.168.1.100:8000/api/market/full_tick?stocks=000001.SH,000001.SZ"

# 板块列表
curl http://192.168.1.100:8000/api/sector/list

# 沪深 A 股成分股
curl "http://192.168.1.100:8000/api/sector/stocks?sector=沪深A股"

# ETF 代码列表
curl http://192.168.1.100:8000/api/etf/list

# 交易日列表
curl "http://192.168.1.100:8000/api/calendar/trading_dates?market=SH"

# 指数成分股权重
curl "http://192.168.1.100:8000/api/instrument/index_weight?index_code=000300.SH"

# 财务数据
curl "http://192.168.1.100:8000/api/financial/data?stocks=000001.SZ&tables=Balance"

# 批量下载历史数据
curl -X POST http://192.168.1.100:8000/api/download/history_data2 \
  -H "Content-Type: application/json" \
  -d '{"stocks": ["000001.SZ", "600519.SH"], "period": "1d"}'

# 下单（需要 API Key）
curl -X POST http://192.168.1.100:8000/api/trading/order \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-key" \
  -d '{"stock_code": "000001.SZ", "order_type": 23, "order_volume": 100}'
```

## Project Structure

```
qmt-bridge/
├── pyproject.toml                  # 项目元数据与依赖
├── .env.example                    # 配置模板
├── scripts/                        # 启动 / 停止脚本
│   ├── start.sh / start.bat        # 前台启动
│   ├── start-nohup.sh              # 后台启动
│   └── stop.sh / stop.bat          # 停止服务
├── src/qmt_bridge/
│   ├── _version.py                 # 版本号
│   ├── server/                     # FastAPI 服务端
│   │   ├── app.py                  # 应用工厂 & 生命周期管理
│   │   ├── cli.py                  # qmt-server CLI 入口
│   │   ├── config.py               # 配置加载
│   │   ├── security.py             # API Key 认证
│   │   ├── scheduler.py            # 后台数据预下载调度
│   │   ├── helpers.py              # 数据转换工具
│   │   ├── models.py               # Pydantic 请求 / 响应模型
│   │   ├── deps.py                 # 依赖注入
│   │   ├── routers/                # REST API 路由 (21 个模块)
│   │   ├── ws/                     # WebSocket 端点 (5 个)
│   │   └── trading/                # 交易模块
│   │       ├── manager.py          # XtTraderManager 生命周期
│   │       └── callbacks.py        # 交易回调
│   └── client/                     # Python 客户端 (22 个 Mixin 模块)
│       ├── __init__.py             # QMTClient 聚合类
│       ├── base.py                 # HTTP 传输层 (stdlib)
│       ├── websocket.py            # WebSocket 订阅
│       └── [feature].py            # 各功能域客户端方法
└── tests/                          # 测试
```

## Authentication

QMT Bridge 支持可选的 API Key 认证机制：

- **交易端点** (`/api/trading/*`, `/api/credit/*`, `/api/fund/*`, `/api/bank/*`) — 设置了 `API_KEY` 时强制认证
- **数据端点** — 默认无需认证，可通过 `QMT_BRIDGE_REQUIRE_AUTH_FOR_DATA=true` 开启
- **认证方式** — HTTP Header `X-API-Key: your-secret-key`

## Security Notice

本项目设计为**仅在可信局域网内使用**。请勿将服务直接暴露到公网。如确有需要，请通过 VPN 或防火墙规则保护访问。

## FAQ

**Q: QMT 客户端必须一直开着吗？**

是的。xtquant 通过 QMT 客户端获取行情数据，客户端关闭后 API 服务将无法返回实时数据。历史数据如果已下载到本地缓存，在脱机模式下仍可通过 `/api/market/local_data` 访问。

**Q: 支持自动下单吗？**

v2.0 起支持。启用交易模块后 (`--trading`)，可通过 `/api/trading/*` 端点进行下单、撤单、批量委托等操作。交易端点强制要求 API Key 认证。

**Q: 非交易时间能用吗？**

可以。历史 K 线、板块成分股等静态数据在非交易时间也能正常获取。实时 tick 和 WebSocket 推送在非交易时间没有数据。

**Q: 数据延迟大吗？**

局域网内 HTTP 请求延迟通常在 1–5ms。实时 tick 通过 WebSocket 推送，延迟取决于 QMT 客户端本身的行情速度。

**Q: 客户端需要安装什么依赖吗？**

基础客户端 (HTTP) 零依赖，仅使用 Python 标准库。如需 WebSocket 订阅功能，安装 `pip install qmt-bridge[client]` 即可。如安装了 pandas，返回结果会自动转为 DataFrame。

## License

[MIT](LICENSE)

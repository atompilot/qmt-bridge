# 快速开始

## 前提条件

### Windows 端（服务端）

- **Python** 3.10+
- **QMT 客户端** — 已安装并获得券商账号密码（需联系客户经理开通 miniQMT 权限）
- **xtquant** — 通常随 QMT 客户端安装，或 `pip install xtquant`

### 网络

- Windows 和你的主力机在同一局域网下（连同一个路由器 / WiFi）
- Windows 防火墙放行本项目使用的端口（默认 8000）

## 1. 安装

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

## 2. 配置

```bash
cp .env.example .env
# 按需编辑 .env
```

详细配置项请参考 [配置参考](configuration.md)。

## 3. 启动 QMT 客户端

打开 QMT，勾选 **"独立交易"** 模式登录，保持窗口运行（可最小化）。

## 4. 启动 API 服务

```bash
# 使用 CLI 命令（推荐）
qmt-server

# 自定义参数
qmt-server --port 8080 --log-level debug

# 启用交易模块
qmt-server --trading --api-key your-secret-key \
    --mini-qmt-path "C:\国金QMT交易端\userdata_mini" \
    --account-id 12345678
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

## 5. 验证

在你的 Mac/Linux 浏览器中访问：

```
http://<Windows局域网IP>:8000/docs
```

看到 Swagger 文档页面即表示服务正常。也可以用 curl 检查：

```bash
curl http://<Windows局域网IP>:8000/api/meta/health
```

## Python 客户端用法

```python
from qmt_bridge import QMTClient

client = QMTClient(host="192.168.1.100", port=8000)

# 历史 K 线
df = client.get_history("000001.SZ", period="1d", count=60)

# 增强版 K 线，前复权
dfs = client.get_history_ex(
    ["000001.SZ", "600519.SH"],
    dividend_type="front",
    count=60,
)

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

### 交易（需要 API Key）

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

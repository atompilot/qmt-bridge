# QMTClient 总览

`QMTClient` 是 QMT Bridge 的 Python 客户端，基于标准库实现，零外部依赖（WebSocket 功能需安装 `websockets`）。

## 安装

```bash
# 零依赖安装（仅 HTTP）
pip install qmt-bridge

# 含 WebSocket 订阅支持
pip install "qmt-bridge[client]"
```

## 快速示例

```python
from qmt_bridge import QMTClient

client = QMTClient(host="192.168.1.100", port=8000)

# 历史 K 线
df = client.get_history("000001.SZ", period="1d", count=60)

# 实时快照
snapshot = client.get_market_snapshot(["000001.SZ", "600519.SH"])

# 交易（需要 API Key）
client = QMTClient(host="192.168.1.100", api_key="your-secret-key")
order_id = client.place_order("000001.SZ", order_type=23, order_volume=100)
```

## 功能模块

| 模块 | 说明 | 主要方法 |
|------|------|---------|
| [行情数据](market.md) | K 线、快照、指数 | `get_history`, `get_history_ex`, `get_market_snapshot` |
| [Tick/L2](tick.md) | 逐笔行情 | `get_l2_quote`, `get_l2_order`, `get_l2_transaction` |
| [板块管理](sector.md) | 板块增删改查 | `get_sector_list`, `get_sector_stocks` |
| [交易日历](calendar.md) | 交易日、节假日 | `get_trading_dates`, `is_trading_date` |
| [财务数据](financial.md) | 财报数据 | `get_financial_data` |
| [合约信息](instrument.md) | 合约详情、权重 | `get_batch_instrument_detail`, `get_index_weight` |
| [期权](option.md) | 期权链、详情 | `get_option_chain`, `get_option_list` |
| [ETF/可转债](etf.md) | ETF、可转债 | `get_etf_list`, `get_cb_list` |
| [期货](futures.md) | 主力/次主力合约 | `get_main_contract` |
| [公式/指标](formula.md) | 公式调用 | `call_formula`, `call_formula_batch` |
| [港股通](hk.md) | 港股通标的 | `get_hk_stock_list` |
| [表格数据](tabular.md) | 通用表格 | `get_tabular_data` |
| [工具方法](utility.md) | 股票名称、搜索 | `get_stock_name`, `search_stocks` |
| [数据下载](download.md) | 触发下载任务 | `download_batch`, `download_financial` |
| [系统元数据](meta.md) | 版本、状态 | `health_check`, `get_markets` |
| [交易](trading.md) | 下单、撤单、查询 | `place_order`, `cancel_order`, `query_positions` |
| [融资融券](credit.md) | 信用交易 | `credit_order`, `query_credit_positions` |
| [资金划转](fund.md) | 资金管理 | `fund_transfer`, `query_available_fund` |
| [约定式交易](smt.md) | SMT 交易 | `smt_order`, `smt_query_compact` |
| [银证转账](bank.md) | 银证互转 | `bank_transfer_in`, `bank_transfer_out` |
| [WebSocket](websocket-client.md) | 实时订阅 | `subscribe_realtime`, `subscribe_whole_quote` |

## 类引用

::: qmt_bridge.client.QMTClient
    options:
      show_root_heading: true
      heading_level: 3
      members: false

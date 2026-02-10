# REST API 端点速查

!!! tip "交互式文档"
    服务运行后，访问 `http://<host>:8000/docs` (Swagger UI) 或 `http://<host>:8000/redoc` (ReDoc) 可获得交互式 API 文档，支持在线测试。

## Legacy 端点（向后兼容）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/history` | 单只股票历史 K 线 |
| GET | `/api/batch_history` | 批量获取多只股票历史数据 |
| GET | `/api/full_tick` | 最新 tick 快照 |
| GET | `/api/sector_stocks` | 板块成分股列表 |
| GET | `/api/instrument_detail` | 股票基本信息 |
| POST | `/api/download` | 触发历史数据下载 |

## Market — 行情数据 `/api/market/*`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/market/snapshot` | 实时行情快照（个股 / 指数） |
| GET | `/api/market/indices` | 主要指数行情概览 |
| GET | `/api/market/history_ex` | 增强版 K 线（除权、填充） |
| GET | `/api/market/local_data` | 仅读本地缓存（离线可用） |
| GET | `/api/market/divid_factors` | 除权因子 |
| GET | `/api/market/market_data` | 通用行情数据查询 |
| GET | `/api/market/market_data3` | 行情数据（dict of DataFrame） |
| GET | `/api/market/full_kline` | 单只股票完整 K 线 |
| GET | `/api/market/fullspeed_orderbook` | 全速 Order Book |
| GET | `/api/market/transactioncount` | 成交笔数 |

## Tick & L2 — 逐笔数据 `/api/tick/*`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/tick/l2_quote` | L2 行情快照 |
| GET | `/api/tick/l2_order` | L2 逐笔委托 |
| GET | `/api/tick/l2_transaction` | L2 逐笔成交 |
| GET | `/api/tick/l2_thousand_quote` | L2 千档行情 |
| GET | `/api/tick/l2_thousand_orderbook` | L2 千档 Order Book |
| GET | `/api/tick/l2_thousand_trade` | L2 千档成交 |

## Sector — 板块管理 `/api/sector/*`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/sector/list` | 所有板块列表 |
| GET | `/api/sector/stocks` | 板块成分股（支持历史日期） |
| GET | `/api/sector/info` | 板块元数据 |
| POST | `/api/sector/create_folder` | 创建板块文件夹 |
| POST | `/api/sector/create` | 创建自定义板块 |
| POST | `/api/sector/add_stocks` | 添加成分股 |
| POST | `/api/sector/remove_stocks` | 移除成分股 |
| DELETE | `/api/sector/remove` | 删除板块 |
| POST | `/api/sector/reset` | 重置板块成分股 |

## Calendar — 交易日历 `/api/calendar/*`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/calendar/trading_dates` | 交易日列表 |
| GET | `/api/calendar/holidays` | 节假日列表 |
| GET | `/api/calendar/trading_calendar` | 完整日历 |
| GET | `/api/calendar/trading_period` | 交易时段 |
| GET | `/api/calendar/is_trading_date` | 日期校验 |
| GET | `/api/calendar/prev_trading_date` | 上一个交易日 |
| GET | `/api/calendar/next_trading_date` | 下一个交易日 |
| GET | `/api/calendar/trading_dates_count` | 交易日计数 |
| GET | `/api/calendar/trading_time` | 交易时间信息 |

## Financial — 财务数据 `/api/financial/*`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/financial/data` | 财务报表数据（资产负债表 / 利润表等） |

## Instrument — 合约信息 `/api/instrument/*`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/instrument/batch_detail` | 批量合约详情 |
| GET | `/api/instrument/type` | 代码类型判断 |
| GET | `/api/instrument/ipo_info` | IPO 信息 |
| GET | `/api/instrument/index_weight` | 指数成分股权重 |
| GET | `/api/instrument/st_history` | ST 历史 |

## Option — 期权 `/api/option/*`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/option/detail` | 期权合约详情 |
| GET | `/api/option/chain` | 标的期权链 |
| GET | `/api/option/list` | 按到期日 / 类型筛选 |
| GET | `/api/option/history_list` | 历史期权列表 |

## ETF & 可转债 `/api/etf/*` `/api/cb/*`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/etf/list` | ETF 代码列表 |
| GET | `/api/etf/info` | ETF 申赎清单 |
| GET | `/api/cb/info` | 可转债信息 |
| GET | `/api/cb/list` | 可转债列表 |
| GET | `/api/cb/detail` | 可转债详情 |
| GET | `/api/cb/conversion_price` | 转股价信息 |
| GET | `/api/cb/bond_info` | 债券信息 |

## Futures — 期货 `/api/futures/*`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/futures/main_contract` | 主力合约 |
| GET | `/api/futures/sec_main_contract` | 次主力合约 |

## Formula — 公式/指标 `/api/formula/*`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/formula/call` | 调用公式（单只股票） |
| POST | `/api/formula/call_batch` | 调用公式（多只股票） |
| POST | `/api/formula/generate_index` | 生成自定义指数 |

## HK — 港股通 `/api/hk/*`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/hk/stock_list` | 港股通标的列表 |
| GET | `/api/hk/connect_stocks` | 按方向筛选（沪港通 / 深港通） |

## Tabular — 表格数据 `/api/tabular/*`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/tabular/data` | 获取表格数据 |
| GET | `/api/tabular/tables` | 列出可用数据表 |

## Utility — 工具方法 `/api/utility/*`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/utility/stock_name` | 获取股票中文名 |
| GET | `/api/utility/batch_stock_name` | 批量获取股票名 |
| GET | `/api/utility/code_to_market` | 代码→市场归属 |
| GET | `/api/utility/search` | 按关键词搜索股票 |

## Meta — 系统元数据 `/api/meta/*`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/meta/health` | 健康检查 |
| GET | `/api/meta/version` | 服务版本 |
| GET | `/api/meta/xtdata_version` | xtquant 版本 |
| GET | `/api/meta/connection_status` | xtdata 连接状态 |
| GET | `/api/meta/markets` | 可用市场列表 |
| GET | `/api/meta/periods` | K 线周期列表 |
| GET | `/api/meta/stock_list` | 按类别获取证券列表 |
| GET | `/api/meta/last_trade_date` | 最近交易日 |
| GET | `/api/meta/quote_server_status` | 行情服务器状态 |

## Download — 数据下载 `/api/download/*`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/download/batch` | 批量下载历史数据 |
| POST | `/api/download/financial` | 下载财务数据 |
| POST | `/api/download/financial2` | 同步下载财务数据（阻塞） |
| POST | `/api/download/sector_data` | 下载板块数据 |
| POST | `/api/download/index_weight` | 下载指数权重 |
| POST | `/api/download/etf_info` | 下载 ETF 信息 |
| POST | `/api/download/cb_data` | 下载可转债数据 |
| POST | `/api/download/history_contracts` | 下载过期合约 |
| POST | `/api/download/ipo_data` | 下载 IPO 数据 |
| POST | `/api/download/option_data` | 下载期权数据 |
| POST | `/api/download/futures_data` | 下载期货数据 |
| POST | `/api/download/holiday` | 下载节假日数据 |

## Trading — 交易 `/api/trading/*` :material-lock:

!!! note "需要认证"
    交易端点需要通过 `X-API-Key` 请求头进行认证，且服务端需启用交易模块 (`--trading`)。

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/trading/order` | 下单 |
| POST | `/api/trading/cancel` | 撤单 |
| POST | `/api/trading/batch_order` | 批量下单 |
| POST | `/api/trading/batch_cancel` | 批量撤单 |
| POST | `/api/trading/order_async` | 异步下单 |
| POST | `/api/trading/cancel_async` | 异步撤单 |
| GET | `/api/trading/orders` | 查询委托 |
| GET | `/api/trading/trades` | 查询成交 |
| GET | `/api/trading/positions` | 查询持仓 |
| GET | `/api/trading/asset` | 查询资产 |
| GET | `/api/trading/order_detail` | 查询单笔委托 |
| GET | `/api/trading/order/{order_id}` | 查询指定委托 |
| GET | `/api/trading/trade/{trade_id}` | 查询指定成交 |
| GET | `/api/trading/position/{stock_code}` | 查询指定持仓 |
| GET | `/api/trading/position_statistics` | 持仓统计 |
| GET | `/api/trading/account_status` | 账户状态 |
| GET | `/api/trading/account_info` | 账户信息 |
| GET | `/api/trading/account_infos` | 全部账户信息 |
| GET | `/api/trading/new_purchase_limit` | 新股申购额度 |
| GET | `/api/trading/ipo_data` | IPO 日历 |
| GET | `/api/trading/com_fund` | COM 资金查询 |
| GET | `/api/trading/com_position` | COM 持仓查询 |
| POST | `/api/trading/export_data` | 导出交易数据 |
| GET | `/api/trading/query_data` | 查询导出数据 |
| POST | `/api/trading/sync_transaction` | 同步外部成交 |

## Credit — 融资融券 `/api/credit/*` :material-lock:

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/credit/order` | 信用交易下单 |
| GET | `/api/credit/positions` | 信用持仓 |
| GET | `/api/credit/asset` | 信用资产 |
| GET | `/api/credit/debt` | 负债查询 |
| GET | `/api/credit/available_amount` | 可用额度 |
| GET | `/api/credit/slo_stocks` | 可融券标的 |
| GET | `/api/credit/fin_stocks` | 可融资标的 |
| GET | `/api/credit/subjects` | 标的证券 |
| GET | `/api/credit/assure` | 担保品信息 |

## Fund — 资金划转 `/api/fund/*` :material-lock:

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/fund/transfer` | 资金划转 |
| GET | `/api/fund/transfer_records` | 划转记录 |
| GET | `/api/fund/available` | 可用资金 |
| POST | `/api/fund/ctp_transfer_in` | CTP 转入 |
| POST | `/api/fund/ctp_transfer_out` | CTP 转出 |
| GET | `/api/fund/ctp_balance` | CTP 余额 |
| POST | `/api/fund/ctp_option_to_future` | 期权→期货划转 |
| POST | `/api/fund/ctp_future_to_option` | 期货→期权划转 |

## SMT — 约定式交易 `/api/smt/*` :material-lock:

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/smt/order` | 约定式下单 |
| POST | `/api/smt/negotiate_order_async` | 异步协商下单 |
| POST | `/api/smt/cancel` | 撤单 |
| GET | `/api/smt/quoter` | 报价方信息 |
| GET | `/api/smt/compact` | 约定合约 |
| GET | `/api/smt/appointment` | 预约信息 |
| GET | `/api/smt/secu_info` | 证券信息 |
| GET | `/api/smt/secu_rate` | 证券费率 |

## Bank — 银证转账 `/api/bank/*` :material-lock:

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/bank/transfer_in` | 银行→证券 |
| POST | `/api/bank/transfer_out` | 证券→银行 |
| GET | `/api/bank/balance` | 银行余额 |
| GET | `/api/bank/transfer_records` | 转账记录 |
| GET | `/api/bank/banks` | 已绑定银行 |
| GET | `/api/bank/transfer_limit` | 转账限额 |
| GET | `/api/bank/available_amount` | 可转金额 |
| GET | `/api/bank/status` | 转账状态 |

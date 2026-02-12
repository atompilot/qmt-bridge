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
| GET | `/api/market/full_tick` | 实时行情快照（个股 / 指数） |
| GET | `/api/market/indices` | 主要指数行情概览 |
| GET | `/api/market/market_data_ex` | 增强版 K 线（除权、填充） |
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
| GET | `/api/tick/l2_thousand_queue` | L2 千档委托队列 |
| GET | `/api/tick/broker_queue` | 经纪商委托队列 |
| GET | `/api/tick/order_rank` | 委托排名 |

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

## Financial — 财务数据 `/api/financial/*`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/financial/data` | 财务报表数据（资产负债表 / 利润表等） |
| GET | `/api/financial/data_ori` | 原始格式财务报表数据 |

## Instrument — 合约信息 `/api/instrument/*`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/instrument/detail_list` | 批量合约详情 |
| GET | `/api/instrument/type` | 代码类型判断 |
| GET | `/api/instrument/ipo_info` | IPO 信息 |
| GET | `/api/instrument/index_weight` | 指数成分股权重 |
| GET | `/api/instrument/his_st_data` | ST 历史 |

## Option — 期权 `/api/option/*`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/option/detail` | 期权合约详情 |
| GET | `/api/option/chain` | 标的期权链 |
| GET | `/api/option/list` | 按到期日 / 类型筛选 |
| GET | `/api/option/his_option_list` | 历史期权列表 |

## ETF `/api/etf/*`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/etf/list` | ETF 代码列表 |
| GET | `/api/etf/info` | ETF 申赎清单 |

## CB — 可转债 `/api/cb/*`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/cb/list` | 可转债列表 |
| GET | `/api/cb/info` | 可转债信息 |

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
| POST | `/api/formula/generate_index_data` | 生成自定义指数 |
| POST | `/api/formula/create` | 创建公式 |
| POST | `/api/formula/import` | 导入公式 |
| DELETE | `/api/formula/delete` | 删除公式 |
| GET | `/api/formula/list` | 公式列表 |

## HK — 港股通 `/api/hk/*`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/hk/stock_list` | 港股通标的列表 |
| GET | `/api/hk/connect_stocks` | 按方向筛选（沪港通 / 深港通） |
| GET | `/api/hk/broker_dict` | 港股经纪商字典 |

## Tabular — 表格数据 `/api/tabular/*`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/tabular/data` | 获取表格数据 |
| GET | `/api/tabular/tables` | 列出可用数据表 |
| GET | `/api/tabular/formula` | 获取表格公式 |

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
| GET | `/api/meta/period_list` | K 线周期列表 |
| GET | `/api/meta/stock_list` | 按类别获取证券列表 |
| GET | `/api/meta/last_trade_date` | 最近交易日 |
| GET | `/api/meta/quote_server_status` | 行情服务器状态 |

## Download — 数据下载 `/api/download/*`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/download/history_data2` | 批量下载历史数据 |
| POST | `/api/download/financial_data` | 下载财务数据 |
| POST | `/api/download/financial_data2` | 同步下载财务数据（阻塞） |
| POST | `/api/download/sector_data` | 下载板块数据 |
| POST | `/api/download/index_weight` | 下载指数权重 |
| POST | `/api/download/etf_info` | 下载 ETF 信息 |
| POST | `/api/download/cb_data` | 下载可转债数据 |
| POST | `/api/download/history_contracts` | 下载过期合约 |
| POST | `/api/download/metatable_data` | 下载合约元数据表 |
| POST | `/api/download/holiday_data` | 下载节假日数据 |
| POST | `/api/download/his_st_data` | 下载历史 ST 数据 |
| POST | `/api/download/tabular_data` | 下载表格数据 |

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
| POST | `/api/trading/cancel_by_sysid` | 按系统编号撤单 |
| POST | `/api/trading/cancel_by_sysid_async` | 按系统编号异步撤单 |
| GET | `/api/trading/orders` | 查询委托 |
| GET | `/api/trading/trades` | 查询成交 |
| GET | `/api/trading/positions` | 查询持仓 |
| GET | `/api/trading/asset` | 查询资产 |
| GET | `/api/trading/order_detail` | 查询单笔委托 |
| GET | `/api/trading/order/{order_id}` | 查询指定委托 |
| GET | `/api/trading/trade/{trade_id}` | 查询指定成交 |
| GET | `/api/trading/position/{stock_code}` | 查询指定持仓 |
| GET | `/api/trading/account_status` | 账户状态 |
| GET | `/api/trading/account_status_detail` | 账户状态详情 |
| GET | `/api/trading/account_infos` | 全部账户信息 |
| GET | `/api/trading/secu_account` | 证券账户信息 |
| GET | `/api/trading/new_purchase_limit` | 新股申购额度 |
| GET | `/api/trading/ipo_data` | IPO 日历 |
| GET | `/api/trading/com_fund` | COM 资金查询 |
| GET | `/api/trading/com_position` | COM 持仓查询 |
| POST | `/api/trading/export_data` | 导出交易数据 |
| POST | `/api/trading/query_data` | 查询导出数据 |
| POST | `/api/trading/sync_transaction` | 同步外部成交 |

## Credit — 融资融券 `/api/credit/*` :material-lock:

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/credit/order` | 信用交易下单 |
| GET | `/api/credit/positions` | 信用持仓 |
| GET | `/api/credit/detail` | 信用资产详情 |
| GET | `/api/credit/stk_compacts` | 负债合约查询 |
| GET | `/api/credit/slo_code` | 可融券标的 |
| GET | `/api/credit/subjects` | 标的证券 |
| GET | `/api/credit/assure` | 担保品信息 |

## Fund — 资金划转 `/api/fund/*` :material-lock:

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/fund/transfer` | 资金划转 |
| POST | `/api/fund/ctp_option_to_future` | 期权→期货划转 |
| POST | `/api/fund/ctp_future_to_option` | 期货→期权划转 |
| POST | `/api/fund/secu_transfer` | 证券划转 |

## SMT — 转融通 `/api/smt/*` :material-lock:

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/smt/quoter` | 报价方信息 |
| GET | `/api/smt/compact` | 转融通合约 |
| GET | `/api/smt/orders` | 转融通委托 |
| POST | `/api/smt/negotiate_order_async` | 异步协商下单 |
| POST | `/api/smt/appointment_order_async` | 异步预约下单 |
| POST | `/api/smt/appointment_cancel_async` | 异步取消预约 |
| POST | `/api/smt/compact_renewal_async` | 异步合约展期 |
| POST | `/api/smt/compact_return_async` | 异步合约归还 |

## Bank — 银证转账 `/api/bank/*` :material-lock:

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/bank/transfer_in` | 银行→证券 |
| POST | `/api/bank/transfer_out` | 证券→银行 |
| POST | `/api/bank/transfer_in_async` | 银行→证券（异步） |
| POST | `/api/bank/transfer_out_async` | 证券→银行（异步） |
| GET | `/api/bank/info` | 银行信息 |
| POST | `/api/bank/amount` | 银行余额查询 |
| GET | `/api/bank/transfer_stream` | 转账流水 |

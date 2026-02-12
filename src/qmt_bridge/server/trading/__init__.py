"""交易子模块 — 管理 XtQuantTrader 的完整生命周期。

本模块封装了 QMT 迅投交易客户端（XtQuantTrader）的连接管理、
委托下单、查询持仓/资产、信用交易、银证转账等功能，
并通过回调桥接机制将后台线程事件转发至 FastAPI 的 asyncio 事件循环。
"""

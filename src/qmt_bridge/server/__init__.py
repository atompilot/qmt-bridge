"""QMT Bridge 服务端包。

本包基于 FastAPI 框架构建，为迅投 miniQMT (xtquant) 提供 RESTful API 桥接层。
核心功能包括：
- 行情数据查询（底层调用 xtquant.xtdata 模块的各类行情接口）
- 交易委托管理（底层调用 xtquant.xttrader 模块的交易接口）
- 实时行情推送（通过 WebSocket 转发 xtdata 的实时订阅数据）
- 通知推送（交易回调事件 -> 飞书/Webhook 通知）

运行环境要求：Windows 系统 + 已安装 xtquant SDK + miniQMT 客户端运行中。
"""

"""WebSocket 处理器子模块。

本模块包含 qmt-bridge 服务端的所有 WebSocket 端点：

- ``realtime``: 实时行情订阅（/ws/realtime）
- ``trade_callback``: 交易事件推送（/ws/trade）
- ``download_progress``: 历史数据下载进度跟踪（/ws/download_progress）
- ``whole_quote``: 全市场行情订阅（/ws/whole_quote）
- ``formula``: 公式指标实时计算（/ws/formula）
- ``l2_thousand``: L2 千档行情订阅（/ws/l2_thousand）

所有 WebSocket 端点都使用 ``asyncio.run_coroutine_threadsafe`` 将
xtdata 后台线程的回调数据桥接到 FastAPI 的 asyncio 事件循环中。
"""

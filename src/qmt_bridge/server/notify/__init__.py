"""通知子模块 — 将交易事件推送到飞书群机器人、通用 Webhook 等外部渠道。

本模块实现了可扩展的通知分发机制：
- ``NotifierManager`` 作为统一入口，管理多个通知后端
- 支持事件类型过滤（白名单/黑名单）
- 内置飞书 Webhook 和通用 HTTP Webhook 两种后端
- 新增通知渠道只需实现 ``NotifierBackend`` 抽象接口
"""

from .base import NotifierManager

__all__ = ["NotifierManager"]

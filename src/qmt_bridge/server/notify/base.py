"""通知后端抽象基类与分发管理器。

本模块定义了通知系统的核心架构：

- ``NotifierBackend``: 抽象基类，定义所有通知后端必须实现的接口
- ``NotifierManager``: 分发管理器，负责：
  1. 根据配置实例化对应的通知后端（飞书/Webhook）
  2. 根据事件类型白名单/黑名单过滤事件
  3. 将事件分发给所有已启用的后端

通知分发流程：
    交易回调事件 → NotifierManager.dispatch() → 事件过滤 → 各 Backend.send()
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from fastapi import APIRouter, HTTPException, Request

if TYPE_CHECKING:
    from ..config import Settings

logger = logging.getLogger("qmt_bridge.notify")

# ---------------------------------------------------------------------
# 抽象基类
# ---------------------------------------------------------------------


class NotifierBackend(ABC):
    """通知后端抽象接口。

    所有通知后端（飞书、Webhook 等）必须实现此接口。
    新增通知渠道时，只需继承此类并实现以下四个方法即可。
    """

    @abstractmethod
    async def start(self) -> None:
        """启动后端（初始化 HTTP 客户端等资源）。"""
        ...

    @abstractmethod
    async def stop(self) -> None:
        """停止后端（释放 HTTP 客户端等资源）。"""
        ...

    @abstractmethod
    async def send(self, event: dict) -> None:
        """发送通知事件。

        Args:
            event: 事件字典，包含 'type' 和 'data' 字段。
        """
        ...

    @abstractmethod
    def name(self) -> str:
        """返回后端名称标识，用于日志和配置识别。"""
        ...


# ---------------------------------------------------------------------
# 分发管理器
# ---------------------------------------------------------------------


class NotifierManager:
    """通知分发管理器，管理多个通知后端并进行事件过滤和分发。

    在整体架构中的作用：
    - 由 BridgeTraderCallback 调用 dispatch() 方法接收交易事件
    - 根据配置的事件类型白名单/黑名单进行过滤
    - 将通过过滤的事件分发给所有已注册的通知后端

    配置方式（通过环境变量）：
    - QMT_BRIDGE_NOTIFY_BACKENDS: 逗号分隔的后端名称（如 "feishu,webhook"）
    - QMT_BRIDGE_NOTIFY_EVENT_TYPES: 事件类型白名单（可选）
    - QMT_BRIDGE_NOTIFY_IGNORE_EVENT_TYPES: 事件类型黑名单（可选）
    """

    def __init__(self, settings: Settings) -> None:
        """初始化通知管理器。

        根据 Settings 配置创建对应的通知后端实例，并解析事件过滤规则。

        Args:
            settings: 应用配置对象，包含通知相关的所有配置项。
        """
        self._backends: list[NotifierBackend] = []
        self._allow: set[str] | None = None   # 事件类型白名单，None 表示允许所有
        self._deny: set[str] = set()           # 事件类型黑名单

        # 解析事件类型白名单（逗号分隔的字符串）
        if settings.notify_event_types:
            self._allow = {
                t.strip()
                for t in settings.notify_event_types.split(",")
                if t.strip()
            }
        # 解析事件类型黑名单
        if settings.notify_ignore_event_types:
            self._deny = {
                t.strip()
                for t in settings.notify_ignore_event_types.split(",")
                if t.strip()
            }

        # 根据配置的后端名称逐个实例化通知后端
        backend_names = [
            n.strip()
            for n in settings.notify_backends.split(",")
            if n.strip()
        ]
        for bname in backend_names:
            backend = self._create_backend(bname, settings)
            if backend is not None:
                self._backends.append(backend)

        if not self._backends:
            logger.warning(
                "Notification enabled but no backends configured "
                "(set QMT_BRIDGE_NOTIFY_BACKENDS)"
            )

    @staticmethod
    def _create_backend(
        name: str, settings: Settings
    ) -> NotifierBackend | None:
        """根据后端名称创建对应的通知后端实例。

        采用工厂模式，根据名称动态导入并实例化后端。

        Args:
            name: 后端名称（'feishu' 或 'webhook'）。
            settings: 应用配置对象。

        Returns:
            通知后端实例，配置不完整或名称未知时返回 None。
        """
        if name == "feishu":
            from .feishu import FeishuWebhookBackend

            if not settings.feishu_webhook_url:
                logger.warning("feishu backend requested but FEISHU_WEBHOOK_URL is empty")
                return None
            return FeishuWebhookBackend(
                webhook_url=settings.feishu_webhook_url,
                secret=settings.feishu_webhook_secret,
            )
        if name == "webhook":
            from .webhook import GenericWebhookBackend

            if not settings.webhook_url:
                logger.warning("webhook backend requested but WEBHOOK_URL is empty")
                return None
            return GenericWebhookBackend(
                webhook_url=settings.webhook_url,
                secret=settings.webhook_secret,
            )
        logger.warning("Unknown notify backend: %s", name)
        return None

    @property
    def backend_names(self) -> list[str]:
        """返回所有已注册后端的名称列表。"""
        return [b.name() for b in self._backends]

    def _should_notify(self, event: dict) -> bool:
        """判断事件是否应该发送通知。

        过滤逻辑：
        1. 如果事件类型在黑名单中，拒绝
        2. 如果配置了白名单且事件类型不在其中，拒绝
        3. 其他情况允许

        Args:
            event: 事件字典。

        Returns:
            True 表示应该发送通知，False 表示应该过滤掉。
        """
        event_type = event.get("type", "")
        if event_type in self._deny:
            return False
        if self._allow is not None and event_type not in self._allow:
            return False
        return True

    async def dispatch(self, event: dict, *, bypass_filter: bool = False) -> None:
        """将事件分发给所有通知后端。

        此方法不会抛出异常 — 单个后端的发送失败不影响其他后端。

        Args:
            event: 事件字典，包含 'type' 和 'data' 字段。
            bypass_filter: 为 True 时跳过事件过滤（用于测试通知）。
        """
        if not bypass_filter and not self._should_notify(event):
            return
        for backend in self._backends:
            try:
                await backend.send(event)
            except Exception:
                logger.exception("Notify backend %s failed", backend.name())

    async def start(self) -> None:
        """启动所有通知后端。

        逐个调用后端的 start() 方法，单个后端启动失败不影响其他后端。
        """
        for backend in self._backends:
            try:
                await backend.start()
                logger.info("Notifier backend started: %s", backend.name())
            except Exception:
                logger.exception("Failed to start notifier backend: %s", backend.name())

    async def stop(self) -> None:
        """停止所有通知后端。

        逐个调用后端的 stop() 方法，释放资源。
        """
        for backend in self._backends:
            try:
                await backend.stop()
                logger.info("Notifier backend stopped: %s", backend.name())
            except Exception:
                logger.exception("Error stopping notifier backend: %s", backend.name())


# ---------------------------------------------------------------------
# 测试端点 — 用于验证通知配置是否正确
# ---------------------------------------------------------------------

router = APIRouter(prefix="/api/notify", tags=["notify"])


@router.post("/test")
async def test_notify(request: Request):
    """发送测试通知到所有已配置的通知后端。

    用于验证通知渠道是否配置正确、能否正常发送消息。
    测试通知会绕过事件类型过滤规则。

    Returns:
        包含发送状态和后端列表的 JSON 响应。

    Raises:
        HTTPException: 通知模块未启用时返回 503。
    """
    notifier: NotifierManager | None = getattr(
        request.app.state, "notifier_manager", None
    )
    if notifier is None:
        raise HTTPException(503, "Notification module not enabled")
    # 构造测试事件，bypass_filter=True 跳过过滤规则
    test_event = {
        "type": "test",
        "data": {"message": "QMT Bridge notification test"},
    }
    await notifier.dispatch(test_event, bypass_filter=True)
    return {"status": "sent", "backends": notifier.backend_names}

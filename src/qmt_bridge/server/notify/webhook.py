"""通用 HTTP Webhook 通知后端 — 将交易事件以 JSON 格式 POST 到指定 URL。

本模块实现了一个通用的 Webhook 通知后端，可以将交易事件原样（JSON 格式）
发送到任意 HTTP 端点。适用于对接自定义告警系统、IM 机器人或其他第三方服务。

与飞书后端不同，本后端直接发送原始事件 JSON，不做格式转换。
"""

from __future__ import annotations

import logging

from .base import NotifierBackend

logger = logging.getLogger("qmt_bridge.notify.webhook")


class GenericWebhookBackend(NotifierBackend):
    """通用 HTTP Webhook 通知后端。

    将交易事件以 JSON 格式 POST 到用户配置的 URL。
    支持通过 X-Webhook-Secret 请求头传递密钥用于接收方验证。

    Attributes:
        _url: 目标 Webhook URL。
        _secret: 密钥字符串，通过 HTTP 头传递给接收方。
        _client: httpx 异步 HTTP 客户端实例。
    """

    def __init__(self, webhook_url: str, secret: str = "") -> None:
        """初始化通用 Webhook 后端。

        Args:
            webhook_url: 目标 Webhook URL，接收 POST 请求。
            secret: 可选密钥，通过 X-Webhook-Secret 请求头传递给接收方。
        """
        self._url = webhook_url
        self._secret = secret
        self._client = None  # type: ignore[assignment]

    def name(self) -> str:
        """返回后端名称标识。"""
        return "webhook"

    async def start(self) -> None:
        """启动后端，创建 httpx 异步 HTTP 客户端。"""
        import httpx

        self._client = httpx.AsyncClient(timeout=10.0)

    async def stop(self) -> None:
        """停止后端，关闭并释放 HTTP 客户端资源。"""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def send(self, event: dict) -> None:
        """将交易事件以 JSON 格式 POST 到目标 URL。

        如果配置了密钥，会通过 X-Webhook-Secret 请求头传递给接收方，
        接收方可据此验证请求来源的合法性。

        Args:
            event: 交易事件字典，将直接作为 JSON 请求体发送。
        """
        if self._client is None:
            logger.warning("Webhook client not started, dropping event")
            return

        headers: dict[str, str] = {"Content-Type": "application/json"}
        # 如果配置了密钥，通过自定义 HTTP 头传递
        if self._secret:
            headers["X-Webhook-Secret"] = self._secret

        resp = await self._client.post(self._url, json=event, headers=headers)
        if resp.status_code >= 400:
            logger.warning(
                "Webhook %s returned %s: %s",
                self._url,
                resp.status_code,
                resp.text[:200],
            )

"""飞书（Lark）群机器人 Webhook 通知后端。

本模块实现了通过飞书自定义机器人 Webhook 发送通知的功能。

特性：
- 支持飞书 v2 签名验证（HMAC-SHA256）
- 内置请求频率限制，避免触发飞书 API 限流
- 使用飞书交互式卡片消息格式，展示结构化的交易事件信息
- 基于 httpx 异步 HTTP 客户端发送请求
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import logging
import time

from .base import NotifierBackend
from .formatters import format_feishu_card

logger = logging.getLogger("qmt_bridge.notify.feishu")

# 两次请求之间的最小间隔（秒），用于防止触发飞书 API 频率限制
_MIN_INTERVAL = 0.5


class FeishuWebhookBackend(NotifierBackend):
    """飞书自定义机器人 Webhook 通知后端。

    通过飞书群机器人 Webhook 接口发送交互式卡片消息。
    支持可选的签名验证以确保消息安全。

    Attributes:
        _url: 飞书 Webhook URL。
        _secret: 签名密钥，为空则不签名。
        _client: httpx 异步 HTTP 客户端实例。
        _last_send: 上次发送请求的时间戳，用于频率控制。
        _lock: 异步锁，确保频率控制的并发安全。
    """

    def __init__(self, webhook_url: str, secret: str = "") -> None:
        """初始化飞书通知后端。

        Args:
            webhook_url: 飞书自定义机器人的 Webhook URL。
            secret: 签名校验密钥（在飞书机器人安全设置中配置），为空则不进行签名。
        """
        self._url = webhook_url
        self._secret = secret
        self._client = None  # type: ignore[assignment]
        self._last_send: float = 0.0
        self._lock = asyncio.Lock()

    def name(self) -> str:
        """返回后端名称标识。"""
        return "feishu"

    async def start(self) -> None:
        """启动后端，创建 httpx 异步 HTTP 客户端。"""
        import httpx

        self._client = httpx.AsyncClient(timeout=10.0)

    async def stop(self) -> None:
        """停止后端，关闭并释放 HTTP 客户端资源。"""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    def _sign(self, timestamp: str) -> str:
        """计算飞书 v2 HMAC-SHA256 签名。

        签名算法：将 "timestamp\\nsecret" 作为 key 进行 HMAC-SHA256 计算，
        然后 Base64 编码。

        Args:
            timestamp: Unix 时间戳字符串。

        Returns:
            Base64 编码的签名字符串。
        """
        string_to_sign = f"{timestamp}\n{self._secret}"
        hmac_code = hmac.new(
            string_to_sign.encode("utf-8"),
            msg=b"",
            digestmod=hashlib.sha256,
        ).digest()
        return base64.b64encode(hmac_code).decode("utf-8")

    async def send(self, event: dict) -> None:
        """将交易事件格式化为飞书卡片消息并发送。

        发送流程：
        1. 频率控制 — 确保两次发送间隔不小于 _MIN_INTERVAL
        2. 格式化 — 将事件转换为飞书交互式卡片消息格式
        3. 签名 — 如果配置了密钥，添加时间戳和签名
        4. 发送 — POST 请求到飞书 Webhook URL
        5. 响应检查 — 记录飞书 API 返回的错误

        Args:
            event: 交易事件字典，包含 'type' 和 'data' 字段。
        """
        if self._client is None:
            logger.warning("Feishu client not started, dropping event")
            return

        async with self._lock:
            # 频率控制：如果距上次发送不足 _MIN_INTERVAL 秒，则等待
            now = time.monotonic()
            elapsed = now - self._last_send
            if elapsed < _MIN_INTERVAL:
                await asyncio.sleep(_MIN_INTERVAL - elapsed)

            # 将事件格式化为飞书交互式卡片消息
            body = format_feishu_card(event)

            # 如果配置了签名密钥，添加时间戳和签名字段
            if self._secret:
                timestamp = str(int(time.time()))
                body["timestamp"] = timestamp
                body["sign"] = self._sign(timestamp)

            resp = await self._client.post(self._url, json=body)
            self._last_send = time.monotonic()

        # 检查 HTTP 响应状态和飞书 API 业务码
        if resp.status_code != 200:
            logger.warning(
                "Feishu webhook returned %s: %s", resp.status_code, resp.text
            )
        else:
            try:
                data = resp.json()
            except Exception:
                logger.warning("Feishu returned non-JSON response: %s", resp.text[:200])
                return
            if data.get("code", 0) != 0:
                logger.warning("Feishu API error: %s", data)

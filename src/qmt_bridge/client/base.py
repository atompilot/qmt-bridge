"""BaseClient — HTTP 传输层，提供认证和基础请求能力。

本模块是所有客户端 Mixin 的基类，封装了与 QMT Bridge 服务端通信所需的
HTTP GET/POST/DELETE 方法，以及 API Key 认证头的构造。

仅依赖 Python 标准库（json, urllib），确保跨平台兼容性。
"""

import json
import urllib.request
from typing import Optional


class BaseClient:
    """轻量级 HTTP/WebSocket 客户端基类。

    所有 Mixin 类（MarketMixin、TradingMixin 等）通过多继承共享本类提供的
    ``_get``、``_post``、``_delete`` 和 ``_headers`` 辅助方法，实现与
    QMT Bridge 服务端的 HTTP 通信。
    """

    def __init__(self, host: str, port: int = 8000, *, api_key: str = ""):
        """初始化客户端连接。

        Args:
            host: QMT Bridge 服务端 IP 地址或主机名，如 ``"192.168.1.100"``
            port: 服务端口，默认 8000
            api_key: API Key，交易端点需要认证时必填
        """
        self.base_url = f"http://{host}:{port}"
        self.ws_url = f"ws://{host}:{port}"
        self.api_key = api_key

    # ------------------------------------------------------------------
    # 内部辅助方法
    # ------------------------------------------------------------------

    def _headers(self) -> dict[str, str]:
        """构造请求头，包含 API Key（如已配置）。

        Returns:
            请求头字典，当设置了 api_key 时会包含 ``X-API-Key`` 字段
        """
        headers: dict[str, str] = {}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    def _get(self, path: str, params: Optional[dict] = None) -> dict:
        """发送 GET 请求并返回解析后的 JSON。

        Args:
            path: API 路径，如 ``"/api/market/full_tick"``
            params: 查询参数字典，值为 None 的键会被跳过

        Returns:
            服务端返回的 JSON 响应（已解析为 dict）
        """
        if params:
            # 将参数编码为 URL 查询字符串，跳过 None 值
            query = "&".join(
                f"{k}={urllib.request.quote(str(v))}"
                for k, v in params.items()
                if v is not None
            )
            url = f"{self.base_url}{path}?{query}"
        else:
            url = f"{self.base_url}{path}"
        req = urllib.request.Request(url, headers=self._headers())
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())

    def _post(self, path: str, body: dict) -> dict:
        """发送 POST 请求（JSON 请求体）并返回解析后的 JSON。

        Args:
            path: API 路径，如 ``"/api/trading/order"``
            body: 请求体字典，会被序列化为 JSON

        Returns:
            服务端返回的 JSON 响应（已解析为 dict）
        """
        url = f"{self.base_url}{path}"
        data = json.dumps(body).encode()
        headers = {"Content-Type": "application/json", **self._headers()}
        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())

    def _delete(self, path: str, params: Optional[dict] = None) -> dict:
        """发送 DELETE 请求并返回解析后的 JSON。

        Args:
            path: API 路径，如 ``"/api/sector/remove"``
            params: 查询参数字典

        Returns:
            服务端返回的 JSON 响应（已解析为 dict）
        """
        if params:
            query = "&".join(
                f"{k}={urllib.request.quote(str(v))}"
                for k, v in params.items()
                if v is not None
            )
            url = f"{self.base_url}{path}?{query}"
        else:
            url = f"{self.base_url}{path}"
        req = urllib.request.Request(url, method="DELETE", headers=self._headers())
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())

    def _to_dataframes(self, data: dict) -> dict:
        """将 ``{stock_code: [records]}`` 格式的数据转换为 ``{stock_code: DataFrame}``。

        当未安装 pandas 时，原样返回 dict 数据，实现优雅降级。

        Args:
            data: 服务端返回的行情数据，键为股票代码，值为记录列表

        Returns:
            安装了 pandas 时返回 ``{str: DataFrame}``，否则原样返回
        """
        try:
            import pandas as pd
        except ImportError:
            return data

        result: dict[str, pd.DataFrame] = {}
        for stock, records in data.items():
            if not records:
                result[stock] = pd.DataFrame()
                continue
            result[stock] = pd.DataFrame(records)
        return result

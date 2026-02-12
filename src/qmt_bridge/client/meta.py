"""MetaMixin — 系统元数据客户端方法。

封装了 QMT Bridge 服务端和 xtquant 系统级信息的查询接口，包括：
- 可用市场和 K 线周期
- 服务端/xtdata 版本信息
- 连接状态和健康检查
- 行情服务器状态

用于监控服务端运行状态和获取系统配置信息。
"""


class MetaMixin:
    """系统元数据客户端方法集合，对应 /api/meta/* 端点。"""

    def get_markets(self) -> dict:
        """获取可用市场列表。

        返回 xtquant 支持的全部市场信息，包括市场代码和名称。
        常见市场: SH（上海）、SZ（深圳）、BJ（北京）、IF（中金所）、
        SF（上期所）、DF（大商所）、ZF（郑商所）、INE（上海能源）等。

        Returns:
            市场信息字典
        """
        resp = self._get("/api/meta/markets")
        return resp.get("markets", {})

    def get_periods(self) -> list:
        """获取可用的 K 线周期列表。

        返回 xtquant 支持的全部 K 线周期，如 ``"tick"``、``"1m"``、
        ``"5m"``、``"15m"``、``"30m"``、``"1h"``、``"1d"``、``"1w"``、``"1mon"`` 等。

        Returns:
            周期字符串列表
        """
        resp = self._get("/api/meta/period_list")
        return resp.get("periods", [])

    def get_stock_list_by_category(self, category: str) -> list[str]:
        """按分类获取股票代码列表。

        底层调用 ``xtdata.get_stock_list_in_sector()``，返回属于指定分类
        的全部股票代码。

        Args:
            category: 分类名称，如 ``"沪深A股"``、``"上证A股"``、``"创业板"``

        Returns:
            股票代码列表
        """
        resp = self._get("/api/meta/stock_list", {"category": category})
        return resp.get("stocks", [])

    def get_last_trade_date(self, market: str) -> str:
        """获取指定市场的最近交易日。

        Args:
            market: 市场代码，如 ``"SH"``

        Returns:
            最近交易日日期字符串
        """
        resp = self._get("/api/meta/last_trade_date", {"market": market})
        return resp.get("last_trade_date", "")

    def get_server_version(self) -> str:
        """获取 QMT Bridge 服务端版本号。

        Returns:
            版本号字符串，如 ``"2.3.0"``
        """
        resp = self._get("/api/meta/version")
        return resp.get("version", "")

    def get_xtdata_version(self) -> str:
        """获取服务端 xtquant/xtdata 库的版本号。

        Returns:
            xtdata 版本字符串
        """
        resp = self._get("/api/meta/xtdata_version")
        return resp.get("xtdata_version", "")

    def get_connection_status(self) -> dict:
        """检查 xtdata 与行情服务器的连接状态。

        底层调用 ``xtdata.get_client()`` 检查连接是否正常。

        Returns:
            连接状态字典，包含 ``connected`` 布尔值等字段
        """
        return self._get("/api/meta/connection_status")

    def health_check(self) -> dict:
        """简单健康检查。

        用于负载均衡器或监控系统探测服务是否存活。

        Returns:
            健康状态字典，包含 ``status`` 字段
        """
        return self._get("/api/meta/health")

    def get_quote_server_status(self) -> dict:
        """获取行情服务器的详细连接状态。

        返回更详细的行情服务器信息，包括连接地址、数据更新时间等。

        Returns:
            行情服务器状态详情字典
        """
        return self._get("/api/meta/quote_server_status")

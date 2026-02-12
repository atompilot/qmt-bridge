"""ETFMixin — ETF 数据客户端方法。

封装了 ETF（交易所交易基金）相关的查询接口。

底层对应 xtquant 的 ``xtdata.get_etf_info()`` 等函数。
"""


class ETFMixin:
    """ETF 数据客户端方法集合，对应 /api/etf/* 端点。"""

    def get_etf_list(self) -> list[str]:
        """获取 ETF 基金代码列表。

        Returns:
            ETF 基金代码列表，如 ``["510050.SH", "159919.SZ", ...]``
        """
        resp = self._get("/api/etf/list")
        return resp.get("stocks", [])

    def get_etf_info(self) -> dict:
        """获取 ETF 申赎信息（申购赎回清单）。

        使用前需先调用 ``download_etf_info()`` 下载数据。

        Returns:
            ETF 申赎信息字典
        """
        resp = self._get("/api/etf/info")
        return resp.get("data", {})

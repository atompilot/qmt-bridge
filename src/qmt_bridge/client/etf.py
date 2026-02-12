"""ETFMixin — ETF 数据客户端方法。

封装了 ETF（交易所交易基金）相关的查询接口。

底层对应 xtquant 的 ETF 信息查询功能。
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

    def get_etf_info(self, stock: str) -> dict:
        """获取单只 ETF 的申赎信息及成分股列表。

        Args:
            stock: ETF 代码，如 ``"510300.SH"``。

        Returns:
            包含 name、nav、component_count、components 等字段的字典。
            components 为成分股列表，每项包含 stock_code 和 volume。
        """
        return self._get("/api/etf/info", params={"stock": stock})

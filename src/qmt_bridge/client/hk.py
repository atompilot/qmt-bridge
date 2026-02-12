"""HKMixin — 港股通数据客户端方法。

封装了港股通（沪港通/深港通）相关的查询接口。

底层对应 xtquant 的 ``xtdata.get_hk_stock_list()`` 等函数。
"""


class HKMixin:
    """港股通数据客户端方法集合，对应 /api/hk/* 端点。"""

    def get_hk_stock_list(self) -> list[str]:
        """获取港股通标的股票列表。

        返回可通过沪港通/深港通渠道交易的全部港股代码。

        Returns:
            港股通股票代码列表
        """
        resp = self._get("/api/hk/stock_list")
        return resp.get("stocks", [])

    def get_hk_connect_stocks(self, connect_type: str = "north") -> list[str]:
        """按方向获取互联互通标的列表。

        Args:
            connect_type: 互联互通方向:
                - ``"north"``: 北向（外资买A股，即沪股通/深股通）
                - ``"south"``: 南向（内资买港股，即港股通）

        Returns:
            标的股票代码列表
        """
        resp = self._get("/api/hk/connect_stocks", {"connect_type": connect_type})
        return resp.get("stocks", [])

    def get_hk_broker_dict(self) -> dict:
        """获取港股经纪商字典。

        Returns:
            经纪商字典数据
        """
        resp = self._get("/api/hk/broker_dict")
        return resp.get("data", {})

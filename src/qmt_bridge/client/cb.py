"""CBMixin — 可转债数据客户端方法。

封装了可转债相关的查询接口。

底层对应 xtquant 的 ``xtdata.get_cb_info()`` 等函数。
"""


class CBMixin:
    """可转债数据客户端方法集合，对应 /api/cb/* 端点。"""

    def get_cb_list(self) -> list[str]:
        """获取全部可转债代码列表。

        Returns:
            可转债代码列表
        """
        resp = self._get("/api/cb/list")
        return resp.get("stocks", [])

    def get_cb_info(self, stock: str) -> dict:
        """获取可转债基本信息。

        Args:
            stock: 可转债代码，如 ``"127045.SZ"``

        Returns:
            可转债基本信息字典
        """
        resp = self._get("/api/cb/info", {"stock": stock})
        return resp.get("data", {})


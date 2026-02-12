"""UtilityMixin — 工具类客户端方法。

封装了常用的辅助查询接口，包括：
- 股票中文名称查询
- 股票代码与市场映射
- 股票搜索（按代码前缀或名称关键字）

底层对应 xtquant 的 ``xtdata.get_instrument_detail()`` 等函数。
"""


class UtilityMixin:
    """工具类客户端方法集合，对应 /api/utility/* 端点。"""

    def get_stock_name(self, stock: str) -> str:
        """获取股票的中文名称。

        Args:
            stock: 股票代码，如 ``"000001.SZ"``

        Returns:
            中文名称，如 ``"平安银行"``
        """
        resp = self._get("/api/utility/stock_name", {"stock": stock})
        return resp.get("name", "")

    def get_batch_stock_name(self, stocks: list[str]) -> dict[str, str]:
        """批量获取股票的中文名称。

        Args:
            stocks: 股票代码列表

        Returns:
            以股票代码为键、中文名称为值的字典，
            如 ``{"000001.SZ": "平安银行", "600519.SH": "贵州茅台"}``
        """
        resp = self._get("/api/utility/batch_stock_name", {"stocks": ",".join(stocks)})
        return resp.get("data", {})

    def code_to_market(self, stock: str) -> dict:
        """判断股票代码所属的市场。

        根据股票代码的后缀（.SH/.SZ/.BJ 等）或编号规则，返回其所属市场信息。

        Args:
            stock: 股票代码

        Returns:
            市场信息字典
        """
        return self._get("/api/utility/code_to_market", {"stock": stock})

    def search_stocks(
        self, keyword: str, category: str = "沪深A股", limit: int = 20
    ) -> list[str]:
        """按关键字搜索股票。

        支持按股票代码前缀或中文名称进行模糊搜索。

        Args:
            keyword: 搜索关键字，如 ``"000001"``、``"平安"``、``"贵州"``
            category: 搜索范围（板块名），如 ``"沪深A股"``
            limit: 最大返回条数

        Returns:
            匹配的股票代码列表
        """
        resp = self._get("/api/utility/search", {
            "keyword": keyword,
            "category": category,
            "limit": limit,
        })
        return resp.get("stocks", [])

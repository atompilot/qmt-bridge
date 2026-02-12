"""TabularMixin — 表格型数据（Metatable）客户端方法。

封装了 xtquant Metatable 系统的查询接口。Metatable 是 xtquant 提供的
结构化数据查询系统，可以访问各类金融数据表（如合约信息表、财务数据表等）。

底层对应 xtquant 的 ``xtdata.get_tabular_data()`` 函数。
"""


class TabularMixin:
    """表格型数据客户端方法集合，对应 /api/tabular/* 端点。"""

    def get_tabular_data(
        self,
        table_name: str,
        stocks: list[str] | None = None,
        start_time: str = "",
        end_time: str = "",
    ) -> dict:
        """从指定数据表中获取数据。

        底层调用 ``xtdata.get_tabular_data()``，根据表名和筛选条件
        查询 Metatable 中的结构化数据。

        Args:
            table_name: 数据表名称（通过 ``list_tables()`` 获取可用表名）
            stocks: 股票代码列表（用于筛选），为 None 则不按股票筛选
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            查询结果数据字典
        """
        resp = self._get("/api/tabular/data", {
            "table_name": table_name,
            "stocks": ",".join(stocks) if stocks else "",
            "start_time": start_time,
            "end_time": end_time,
        })
        return resp.get("data", {})

    def list_tables(self) -> list:
        """获取可用的数据表列表。

        Returns:
            数据表名称列表
        """
        resp = self._get("/api/tabular/tables")
        return resp.get("tables", [])

    def get_tabular_formula(
        self,
        table_name: str,
        stocks: list[str] | None = None,
        start_time: str = "",
        end_time: str = "",
    ) -> dict:
        """按表名查询公式表格数据。

        Args:
            table_name: 数据表名称
            stocks: 股票代码列表
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            公式表格数据字典
        """
        resp = self._get("/api/tabular/formula", {
            "table_name": table_name,
            "stocks": ",".join(stocks) if stocks else "",
            "start_time": start_time,
            "end_time": end_time,
        })
        return resp.get("data", {})

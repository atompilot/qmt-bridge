"""FinancialMixin — 财务数据客户端方法。

封装了上市公司财务报表数据的查询和下载接口。

底层对应 xtquant 的 ``xtdata.get_financial_data()`` 和
``xtdata.download_financial_data()`` 函数。

支持的财务表:
    - ``"Balance"``: 资产负债表
    - ``"Income"``: 利润表
    - ``"CashFlow"``: 现金流量表
    - ``"Capital"``: 股本结构表
    - ``"Holdernum"``: 股东人数表
    - ``"Top10holder"``: 十大股东表
    - ``"Top10flowholder"``: 十大流通股东表
    - ``"Pershareindex"``: 每股指标表
"""


class FinancialMixin:
    """财务数据客户端方法集合，对应 /api/financial/* 端点。"""

    def get_financial_data(
        self,
        stocks: list[str],
        tables: list[str] | None = None,
        start_time: str = "",
        end_time: str = "",
        report_type: str = "report_time",
    ) -> dict:
        """获取上市公司财务报表数据。

        底层调用 ``xtdata.get_financial_data()``，返回指定股票在时间范围内的
        财务报表数据。需要先通过 ``download_financial()`` 下载数据到服务端。

        Args:
            stocks: 股票代码列表，如 ``["000001.SZ", "600519.SH"]``
            tables: 财务表名列表，如 ``["Balance", "Income"]``；为 None 时返回全部
            start_time: 开始时间，格式 ``"20230101"``
            end_time: 结束时间
            report_type: 报表时间类型:
                - ``"report_time"``: 按报告期筛选
                - ``"announce_time"``: 按公告日期筛选

        Returns:
            嵌套字典 ``{stock: {table: [records]}}``
        """
        resp = self._get("/api/financial/data", {
            "stocks": ",".join(stocks),
            "tables": ",".join(tables) if tables else "",
            "start_time": start_time,
            "end_time": end_time,
            "report_type": report_type,
        })
        return resp.get("data", {})

    def download_financial(
        self,
        stocks: list[str],
        tables: list[str] | None = None,
        start_time: str = "",
        end_time: str = "",
    ) -> dict:
        """触发服务端异步下载财务数据。

        底层调用 ``xtdata.download_financial_data()``，向行情服务器请求
        下载指定股票的财务报表数据到服务端本地缓存。

        Args:
            stocks: 股票代码列表
            tables: 财务表名列表，为空则下载全部表
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            下载任务状态信息
        """
        return self._post("/api/download/financial_data", {
            "stocks": stocks,
            "tables": tables or [],
            "start_time": start_time,
            "end_time": end_time,
        })

    def get_financial_data_ori(
        self,
        stocks: list[str],
        tables: list[str] | None = None,
        start_time: str = "",
        end_time: str = "",
        report_type: str = "report_time",
    ) -> dict:
        """获取原始格式财务数据。

        Args:
            stocks: 股票代码列表
            tables: 财务表名列表，为 None 时返回全部
            start_time: 开始时间
            end_time: 结束时间
            report_type: 报表时间类型

        Returns:
            原始格式财务数据
        """
        resp = self._get("/api/financial/data_ori", {
            "stocks": ",".join(stocks),
            "tables": ",".join(tables) if tables else "",
            "start_time": start_time,
            "end_time": end_time,
            "report_type": report_type,
        })
        return resp.get("data", {})

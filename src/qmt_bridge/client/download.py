"""DownloadMixin — 数据下载客户端方法。

封装了向服务端发起各类数据下载任务的接口。下载的数据会缓存在服务端本地，
后续可通过 ``get_local_data()`` 等方法直接读取。

底层对应 xtquant 的 ``xtdata.download_history_data2()``、
``xtdata.download_sector_data()``、``xtdata.download_financial_data2()`` 等函数。

典型使用流程:
    1. 调用 ``download_batch()`` 下载历史行情数据
    2. 调用 ``get_local_data()`` 读取已下载的数据

注意: 部分下载接口为异步操作，会在后台执行；部分为同步阻塞操作。

服务端自动预下载:
    服务端通过 scheduler 模块在启动时自动执行以下 6 个下载任务，之后每 24 小时
    定时刷新。因此客户端通常无需手动调用这些方法：

    - ``download_sector_data()``       — 板块成分数据
    - ``download_holiday_data()``      — 节假日日历数据
    - ``download_history_contracts()`` — 历史合约数据
    - ``download_index_weight()``      — 指数成分权重
    - ``download_etf_info()``          — ETF 申赎信息
    - ``download_cb_data()``           — 可转债数据
"""


class DownloadMixin:
    """数据下载客户端方法集合，对应 /api/download/* 端点。"""

    def download_batch(
        self,
        stocks: list[str],
        period: str = "1d",
        start_time: str = "",
        end_time: str = "",
    ) -> dict:
        """触发服务端批量下载历史行情数据。

        底层调用 ``xtdata.download_history_data2()``，向行情服务器请求下载
        指定股票在时间范围内的历史 K 线数据到服务端本地。

        此接口为异步操作，下载任务在服务端后台执行。可通过 WebSocket
        ``/ws/download_progress`` 端点实时跟踪下载进度。

        Args:
            stocks: 股票代码列表，如 ``["000001.SZ", "600519.SH"]``
            period: K 线周期，如 ``"1d"``/``"1m"``/``"5m"``
            start_time: 开始时间，格式 ``"20230101"``
            end_time: 结束时间，格式同上

        Returns:
            下载任务状态信息
        """
        return self._post("/api/download/history_data2", {
            "stocks": stocks,
            "period": period,
            "start_time": start_time,
            "end_time": end_time,
        })

    def download_sector_data(self) -> dict:
        """下载板块成分数据。

        底层调用 ``xtdata.download_sector_data()``，下载全部板块（行业/概念等）
        的成分股数据到服务端本地。建议定期执行以保持板块数据最新。

        Note:
            服务端会在启动时自动执行此下载，之后每 24 小时定时刷新，
            客户端通常无需手动调用。

        Returns:
            下载结果信息
        """
        return self._post("/api/download/sector_data", {})

    def download_index_weight(self) -> dict:
        """下载指数成分权重数据。

        底层调用 ``xtdata.download_index_weight()``，下载全部指数的成分股
        权重数据。下载后可通过 ``get_index_weight()`` 查询。

        Note:
            服务端会在启动时自动执行此下载，之后每 24 小时定时刷新，
            客户端通常无需手动调用。

        Returns:
            下载结果信息
        """
        return self._post("/api/download/index_weight", {})

    def download_etf_info(self) -> dict:
        """下载 ETF 申赎信息。

        底层调用 ``xtdata.download_etf_info()``，下载 ETF 基金的申购赎回清单
        数据。下载后可通过 ``get_etf_info()`` 查询。

        Note:
            服务端会在启动时自动执行此下载，之后每 24 小时定时刷新，
            客户端通常无需手动调用。

        Returns:
            下载结果信息
        """
        return self._post("/api/download/etf_info", {})

    def download_cb_data(self) -> dict:
        """下载可转债数据。

        底层调用 ``xtdata.download_cb_data()``，下载全部可转债的基本信息
        和转股价格等数据。

        Note:
            服务端会在启动时自动执行此下载，之后每 24 小时定时刷新，
            客户端通常无需手动调用。

        Returns:
            下载结果信息
        """
        return self._post("/api/download/cb_data", {})

    def download_history_contracts(self) -> dict:
        """下载历史合约数据（含已到期合约）。

        底层调用 ``xtdata.download_history_contracts()``，下载已到期的
        期货/期权合约列表数据，用于历史数据回测。

        Note:
            服务端会在启动时自动执行此下载，之后每 24 小时定时刷新，
            客户端通常无需手动调用。

        Returns:
            下载结果信息
        """
        return self._post("/api/download/history_contracts", {})

    def download_financial_data2(
        self, stocks: list[str], tables: list[str] | None = None
    ) -> dict:
        """同步下载财务数据（阻塞直至完成）。

        底层调用 ``xtdata.download_financial_data2()``，与异步版本
        ``download_financial()`` 不同，此方法会阻塞等待下载完成后再返回。

        Args:
            stocks: 股票代码列表
            tables: 财务表名列表，如 ``["Balance", "Income"]``，为空则下载全部

        Returns:
            下载结果信息
        """
        return self._post("/api/download/financial_data2", {
            "stocks": stocks,
            "tables": tables or [],
        })

    def download_metatable_data(self) -> dict:
        """下载合约元数据表（期货合约品种信息）。

        底层调用 ``xtdata.download_metatable_data()``，下载期货等品种的
        合约元数据信息表。

        **重要**: 在查询期货合约列表或获取主力合约前必须先调用此方法，
        否则无法识别期货品种。

        Returns:
            下载结果信息
        """
        return self._post("/api/download/metatable_data", {})

    def download_holiday_data(self) -> dict:
        """下载节假日日历数据。

        底层调用 ``xtdata.download_holiday_data()``，下载交易所公布的
        节假日日历数据到服务端。

        Note:
            服务端会在启动时自动执行此下载，之后每 24 小时定时刷新，
            客户端通常无需手动调用。

        Returns:
            下载结果信息
        """
        return self._post("/api/download/holiday_data", {})

    def download_his_st_data(
        self,
        stocks: list[str],
        period: str = "1d",
        start_time: str = "",
        end_time: str = "",
    ) -> dict:
        """下载历史 ST 数据。

        底层调用 ``xtdata.download_his_st_data()``，下载指定股票在时间范围内的
        历史 ST（特别处理）标记数据到服务端本地。

        Args:
            stocks: 股票代码列表，如 ``["000001.SZ", "600519.SH"]``
            period: K 线周期，如 ``"1d"``/``"1m"``/``"5m"``
            start_time: 开始时间，格式 ``"20230101"``
            end_time: 结束时间，格式同上

        Returns:
            下载结果信息
        """
        return self._post("/api/download/his_st_data", {
            "stock_list": stocks,
            "period": period,
            "start_time": start_time,
            "end_time": end_time,
        })

    def download_tabular_data(self, tables: list[str]) -> dict:
        """下载表格数据。

        底层调用 ``xtdata.download_tabular_data()``，下载指定表名的表格数据
        到服务端本地。此方法为同步阻塞操作，会等待下载完成后返回。

        Args:
            tables: 需要下载的表名列表

        Returns:
            下载结果信息
        """
        return self._post("/api/download/tabular_data", {
            "table_list": tables,
        })

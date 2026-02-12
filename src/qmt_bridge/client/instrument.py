"""InstrumentMixin — 合约/证券信息客户端方法。

封装了证券合约基本信息的查询接口，包括：
- 合约详情（名称、上市日期、涨跌停价等）
- 合约类型判断
- IPO 信息
- 指数成分权重
- ST 历史记录

底层对应 xtquant 的 ``xtdata.get_instrument_detail()``、
``xtdata.get_instrument_type()``、``xtdata.get_index_weight()`` 等函数。
"""


class InstrumentMixin:
    """合约/证券信息客户端方法集合，对应 /api/instrument/* 端点。"""

    def get_batch_instrument_detail(
        self, stocks: list[str], iscomplete: bool = False
    ) -> dict:
        """批量获取合约详情信息。

        底层调用 ``xtdata.get_instrument_detail_list()``，返回多只股票/期货/期权
        的合约基本信息，包括名称、上市日期、到期日、涨跌停价格等。

        Args:
            stocks: 合约代码列表，如 ``["000001.SZ", "IF2312.IF"]``
            iscomplete: 是否返回完整信息（True 时包含更多字段）

        Returns:
            以合约代码为键的详情字典
        """
        resp = self._get("/api/instrument/detail_list", {
            "stocks": ",".join(stocks),
            "iscomplete": iscomplete,
        })
        return resp.get("data", {})

    def get_instrument_type(self, stock: str) -> str:
        """判断合约类型。

        底层调用 ``xtdata.get_instrument_type()``，返回合约所属的品种类型。

        Args:
            stock: 合约代码，如 ``"000001.SZ"``

        Returns:
            合约类型字符串，如 ``"stock"``（股票）、``"future"``（期货）、
            ``"option"``（期权）、``"index"``（指数）、``"fund"``（基金）等
        """
        resp = self._get("/api/instrument/type", {"stock": stock})
        return resp.get("type", "")

    def get_ipo_info(self, start_time: str = "", end_time: str = "") -> dict:
        """获取 IPO（新股/新债）申购信息。

        底层调用 ``xtdata.get_ipo_info()``，返回指定时间范围内的
        新股发行和可转债发行信息。

        Args:
            start_time: 开始时间，格式 ``"20230101"``
            end_time: 结束时间

        Returns:
            IPO 信息字典
        """
        resp = self._get("/api/instrument/ipo_info", {
            "start_time": start_time,
            "end_time": end_time,
        })
        return resp.get("data", {})

    def get_index_weight(self, index_code: str) -> dict:
        """获取指数成分股权重。

        底层调用 ``xtdata.get_index_weight()``，返回指定指数的全部成分股
        及其权重信息。使用前需先调用 ``download_index_weight()`` 下载数据。

        Args:
            index_code: 指数代码，如 ``"000300.SH"``（沪深300）

        Returns:
            以成分股代码为键、权重为值的字典
        """
        resp = self._get("/api/instrument/index_weight", {"index_code": index_code})
        return resp.get("data", {})

    def get_st_history(self, stock: str) -> dict:
        """获取股票的 ST 历史记录。

        底层调用 ``xtdata.download_his_st_data()``，返回股票被标记为
        ST（特别处理）、*ST（退市风险警示）的历史记录，包括
        被 ST 和摘帽的日期。

        Args:
            stock: 股票代码，如 ``"000001.SZ"``

        Returns:
            ST 历史记录字典
        """
        resp = self._get("/api/instrument/his_st_data", {"stock": stock})
        return resp.get("data", {})

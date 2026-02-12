"""FuturesMixin — 期货数据客户端方法。

封装了期货合约相关的查询接口，主要用于获取主力合约和次主力合约信息。

底层对应 xtquant 的 ``xtdata.get_main_contract()`` 函数。

注意: 使用前需先调用 ``download_metatable_data()`` 下载合约元数据表，
否则无法正确识别期货品种和合约。
"""


class FuturesMixin:
    """期货数据客户端方法集合，对应 /api/futures/* 端点。"""

    def get_main_contract(
        self, code_market: str, start_time: str = "", end_time: str = ""
    ) -> dict:
        """获取期货品种的主力合约。

        底层调用 ``xtdata.get_main_contract()``，返回指定期货品种在时间范围内
        的主力合约代码。主力合约通常是持仓量最大的合约。

        Args:
            code_market: 期货品种代码+市场，如 ``"IF.IF"``（沪深300股指期货）、
                ``"rb.SF"``（螺纹钢）、``"au.SF"``（黄金）
            start_time: 开始时间，格式 ``"20230101"``
            end_time: 结束时间

        Returns:
            主力合约数据字典，包含各时间点对应的主力合约代码
        """
        resp = self._get("/api/futures/main_contract", {
            "code_market": code_market,
            "start_time": start_time,
            "end_time": end_time,
        })
        return resp.get("data", {})

    def get_sec_main_contract(
        self, code_market: str, start_time: str = "", end_time: str = ""
    ) -> dict:
        """获取期货品种的次主力合约。

        底层调用 ``xtdata.get_sec_main_contract()``，返回指定期货品种在
        时间范围内的次主力合约代码。次主力合约通常是持仓量第二大的合约。

        Args:
            code_market: 期货品种代码+市场，如 ``"IF.IF"``
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            次主力合约数据字典
        """
        resp = self._get("/api/futures/sec_main_contract", {
            "code_market": code_market,
            "start_time": start_time,
            "end_time": end_time,
        })
        return resp.get("data", {})

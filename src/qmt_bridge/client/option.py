"""OptionMixin — 期权数据客户端方法。

封装了期权合约相关的查询接口，包括：
- 期权合约详情
- 期权链（T 型报价）
- 期权列表筛选

底层对应 xtquant 的 ``xtdata.get_option_detail()``、
``xtdata.get_option_chain()``、``xtdata.get_option_list()`` 等函数。
"""


class OptionMixin:
    """期权数据客户端方法集合，对应 /api/option/* 端点。"""

    def get_option_detail(self, option_code: str) -> dict:
        """获取期权合约详情。

        底层调用 ``xtdata.get_option_detail()``，返回期权合约的详细信息，
        包括标的代码、行权价、到期日、合约乘数、期权类型等。

        Args:
            option_code: 期权合约代码，如 ``"10005765.SHO"``

        Returns:
            期权合约详情字典
        """
        resp = self._get("/api/option/detail", {"option_code": option_code})
        return resp.get("data", {})

    def get_option_chain(self, undl_code: str) -> dict:
        """获取标的的完整期权链（T 型报价）。

        底层调用 ``xtdata.get_option_chain()``，返回指定标的资产的全部
        期权合约，按到期日和行权价组织为 T 型结构。

        Args:
            undl_code: 标的资产代码，如 ``"510050.SH"``（50ETF）

        Returns:
            期权链数据字典，按到期月份和行权价组织
        """
        resp = self._get("/api/option/chain", {"undl_code": undl_code})
        return resp.get("data", {})

    def get_option_list(
        self,
        undl_code: str,
        dedate: str,
        opttype: str = "",
        isavailable: bool = False,
    ) -> list:
        """按条件筛选期权合约列表。

        底层调用 ``xtdata.get_option_list()``，根据标的、到期日、
        期权类型等条件筛选期权合约。

        Args:
            undl_code: 标的资产代码
            dedate: 到期月份，格式 ``"2312"``（2023年12月）
            opttype: 期权类型 — ``"CALL"``/``"PUT"``，为空则返回全部
            isavailable: 仅返回当前可交易的合约

        Returns:
            期权合约代码列表
        """
        resp = self._get("/api/option/list", {
            "undl_code": undl_code,
            "dedate": dedate,
            "opttype": opttype,
            "isavailable": isavailable,
        })
        return resp.get("data", [])

    def get_history_option_list(self, undl_code: str, dedate: str) -> list:
        """获取历史期权合约列表（含已到期合约）。

        底层调用 ``xtdata.get_history_option_list()``，返回包括已到期
        合约在内的历史期权列表，适合期权历史数据分析。

        Args:
            undl_code: 标的资产代码
            dedate: 到期月份

        Returns:
            历史期权合约代码列表
        """
        resp = self._get("/api/option/his_option_list", {
            "undl_code": undl_code,
            "dedate": dedate,
        })
        return resp.get("data", [])

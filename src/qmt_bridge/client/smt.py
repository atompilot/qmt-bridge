"""SMTMixin — 约定式交易（SMT）客户端方法。

对齐 xttrader 真实 SMT API：
- smt_query_quoter — 查询报价方
- smt_query_compact — 查询约定合约
- smt_query_order — 查询 SMT 委托
- smt_negotiate_order_async — 协商下单
- smt_appointment_order_async — 预约委托
- smt_appointment_cancel_async — 取消预约
- smt_compact_renewal_async — 合约展期
- smt_compact_return_async — 合约归还

底层对应 xtquant 的 ``XtQuantTrader`` 类的 SMT 相关方法。
"""


class SMTMixin:
    """约定式交易客户端方法集合，对应 /api/smt/* 端点。"""

    def smt_query_quoter(self, account_id: str = "") -> dict:
        """查询报价方信息。

        Args:
            account_id: 交易账户 ID

        Returns:
            报价方信息
        """
        return self._get("/api/smt/quoter", {"account_id": account_id})

    def smt_query_compact(self, account_id: str = "") -> dict:
        """查询约定合约列表。

        Args:
            account_id: 交易账户 ID

        Returns:
            约定合约列表
        """
        return self._get("/api/smt/compact", {"account_id": account_id})

    def smt_query_order(self, account_id: str = "") -> dict:
        """查询 SMT 委托列表。

        Args:
            account_id: 交易账户 ID

        Returns:
            SMT 委托列表
        """
        return self._get("/api/smt/orders", {"account_id": account_id})

    def smt_negotiate_order_async(
        self,
        src_group_id: str,
        order_code: str,
        date: str,
        amount: float,
        apply_rate: float,
        dict_param: dict | None = None,
        account_id: str = "",
    ) -> dict:
        """异步协商下单。

        Args:
            src_group_id: 源分组 ID
            order_code: 委托代码
            date: 日期
            amount: 金额
            apply_rate: 申请利率
            dict_param: 附加参数字典
            account_id: 交易账户 ID

        Returns:
            包含请求序号的字典
        """
        return self._post("/api/smt/negotiate_order_async", {
            "src_group_id": src_group_id,
            "order_code": order_code,
            "date": date,
            "amount": amount,
            "apply_rate": apply_rate,
            "dict_param": dict_param or {},
            "account_id": account_id,
        })

    def smt_appointment_order_async(
        self,
        order_code: str,
        date: str,
        amount: float,
        apply_rate: float,
        account_id: str = "",
    ) -> dict:
        """异步预约委托。

        Args:
            order_code: 委托代码
            date: 日期
            amount: 金额
            apply_rate: 申请利率
            account_id: 交易账户 ID

        Returns:
            包含请求序号的字典
        """
        return self._post("/api/smt/appointment_order_async", {
            "order_code": order_code,
            "date": date,
            "amount": amount,
            "apply_rate": apply_rate,
            "account_id": account_id,
        })

    def smt_appointment_cancel_async(
        self, apply_id: str, account_id: str = ""
    ) -> dict:
        """异步取消预约。

        Args:
            apply_id: 预约申请 ID
            account_id: 交易账户 ID

        Returns:
            包含请求序号的字典
        """
        return self._post("/api/smt/appointment_cancel_async", {
            "apply_id": apply_id,
            "account_id": account_id,
        })

    def smt_compact_renewal_async(
        self,
        cash_compact_id: str,
        order_code: str,
        defer_days: int,
        defer_num: int,
        apply_rate: float,
        account_id: str = "",
    ) -> dict:
        """异步合约展期。

        Args:
            cash_compact_id: 现金合约 ID
            order_code: 委托代码
            defer_days: 展期天数
            defer_num: 展期数量
            apply_rate: 申请利率
            account_id: 交易账户 ID

        Returns:
            包含请求序号的字典
        """
        return self._post("/api/smt/compact_renewal_async", {
            "cash_compact_id": cash_compact_id,
            "order_code": order_code,
            "defer_days": defer_days,
            "defer_num": defer_num,
            "apply_rate": apply_rate,
            "account_id": account_id,
        })

    def smt_compact_return_async(
        self,
        src_group_id: str,
        cash_compact_id: str,
        order_code: str,
        occur_amount: float,
        account_id: str = "",
    ) -> dict:
        """异步合约归还。

        Args:
            src_group_id: 源分组 ID
            cash_compact_id: 现金合约 ID
            order_code: 委托代码
            occur_amount: 发生金额
            account_id: 交易账户 ID

        Returns:
            包含请求序号的字典
        """
        return self._post("/api/smt/compact_return_async", {
            "src_group_id": src_group_id,
            "cash_compact_id": cash_compact_id,
            "order_code": order_code,
            "occur_amount": occur_amount,
            "account_id": account_id,
        })

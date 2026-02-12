"""BankMixin — 银证转账客户端方法。

对齐 xttrader 真实银证转账 API：
- bank_transfer_in / bank_transfer_out（同步/异步）
- query_bank_info — 查询绑定银行
- query_bank_amount — 查询银行余额
- query_bank_transfer_stream — 查询转账流水

底层对应 xtquant 的 ``XtQuantTrader`` 类的银证转账方法。
"""


class BankMixin:
    """银证转账客户端方法集合，对应 /api/bank/* 端点。"""

    def bank_transfer_in(
        self,
        bank_no: str,
        bank_account: str,
        balance: float,
        bank_pwd: str = "",
        fund_pwd: str = "",
        account_id: str = "",
    ) -> dict:
        """银行转证券（银转证）。

        Args:
            bank_no: 银行编号
            bank_account: 银行账号
            balance: 转入金额（元）
            bank_pwd: 银行密码
            fund_pwd: 资金密码
            account_id: 交易账户 ID

        Returns:
            转账结果
        """
        return self._post("/api/bank/transfer_in", {
            "bank_no": bank_no,
            "bank_account": bank_account,
            "balance": balance,
            "bank_pwd": bank_pwd,
            "fund_pwd": fund_pwd,
            "account_id": account_id,
        })

    def bank_transfer_out(
        self,
        bank_no: str,
        bank_account: str,
        balance: float,
        bank_pwd: str = "",
        fund_pwd: str = "",
        account_id: str = "",
    ) -> dict:
        """证券转银行（证转银）。

        Args:
            bank_no: 银行编号
            bank_account: 银行账号
            balance: 转出金额（元）
            bank_pwd: 银行密码
            fund_pwd: 资金密码
            account_id: 交易账户 ID

        Returns:
            转账结果
        """
        return self._post("/api/bank/transfer_out", {
            "bank_no": bank_no,
            "bank_account": bank_account,
            "balance": balance,
            "bank_pwd": bank_pwd,
            "fund_pwd": fund_pwd,
            "account_id": account_id,
        })

    def bank_transfer_in_async(
        self,
        bank_no: str,
        bank_account: str,
        balance: float,
        bank_pwd: str = "",
        fund_pwd: str = "",
        account_id: str = "",
    ) -> dict:
        """异步银行转证券（结果通过 WebSocket 回调返回）。

        Args:
            bank_no: 银行编号
            bank_account: 银行账号
            balance: 转入金额（元）
            bank_pwd: 银行密码
            fund_pwd: 资金密码
            account_id: 交易账户 ID

        Returns:
            包含请求序号的字典
        """
        return self._post("/api/bank/transfer_in_async", {
            "bank_no": bank_no,
            "bank_account": bank_account,
            "balance": balance,
            "bank_pwd": bank_pwd,
            "fund_pwd": fund_pwd,
            "account_id": account_id,
        })

    def bank_transfer_out_async(
        self,
        bank_no: str,
        bank_account: str,
        balance: float,
        bank_pwd: str = "",
        fund_pwd: str = "",
        account_id: str = "",
    ) -> dict:
        """异步证券转银行（结果通过 WebSocket 回调返回）。

        Args:
            bank_no: 银行编号
            bank_account: 银行账号
            balance: 转出金额（元）
            bank_pwd: 银行密码
            fund_pwd: 资金密码
            account_id: 交易账户 ID

        Returns:
            包含请求序号的字典
        """
        return self._post("/api/bank/transfer_out_async", {
            "bank_no": bank_no,
            "bank_account": bank_account,
            "balance": balance,
            "bank_pwd": bank_pwd,
            "fund_pwd": fund_pwd,
            "account_id": account_id,
        })

    def query_bank_info(self, account_id: str = "") -> dict:
        """查询绑定银行信息。

        Args:
            account_id: 交易账户 ID

        Returns:
            绑定银行信息
        """
        return self._get("/api/bank/info", {"account_id": account_id})

    def query_bank_amount(
        self,
        bank_no: str,
        bank_account: str,
        bank_pwd: str,
        account_id: str = "",
    ) -> dict:
        """查询银行余额（POST 因含密码）。

        Args:
            bank_no: 银行编号
            bank_account: 银行账号
            bank_pwd: 银行密码
            account_id: 交易账户 ID

        Returns:
            银行余额信息
        """
        return self._post("/api/bank/amount", {
            "bank_no": bank_no,
            "bank_account": bank_account,
            "bank_pwd": bank_pwd,
            "account_id": account_id,
        })

    def query_bank_transfer_stream(
        self,
        start_date: str,
        end_date: str,
        bank_no: str = "",
        bank_account: str = "",
        account_id: str = "",
    ) -> dict:
        """查询银证转账流水。

        Args:
            start_date: 开始日期
            end_date: 结束日期
            bank_no: 银行编号（可选过滤）
            bank_account: 银行账号（可选过滤）
            account_id: 交易账户 ID

        Returns:
            转账流水记录
        """
        return self._get("/api/bank/transfer_stream", {
            "start_date": start_date,
            "end_date": end_date,
            "bank_no": bank_no,
            "bank_account": bank_account,
            "account_id": account_id,
        })

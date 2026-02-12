"""FundMixin — 资金划转客户端方法。

对齐 xttrader 真实资金划转 API：
- fund_transfer — 账户间资金划转
- ctp_transfer_option_to_future — 期权→期货（双账户 ID）
- ctp_transfer_future_to_option — 期货→期权（双账户 ID）
- secu_transfer — 证券划转

底层对应 xtquant 的 ``XtQuantTrader`` 类的资金划转方法。
"""


class FundMixin:
    """资金划转客户端方法集合，对应 /api/fund/* 端点。"""

    def fund_transfer(
        self, transfer_direction: int, amount: float, account_id: str = ""
    ) -> dict:
        """执行资金划转。

        Args:
            transfer_direction: 划转方向 — 0=转入, 1=转出
            amount: 划转金额（元）
            account_id: 交易账户 ID

        Returns:
            划转结果
        """
        return self._post("/api/fund/transfer", {
            "transfer_direction": transfer_direction,
            "amount": amount,
            "account_id": account_id,
        })

    def ctp_transfer_option_to_future(
        self, opt_account_id: str, ft_account_id: str, balance: float
    ) -> dict:
        """从期权账户划转资金到期货账户（跨市场划转）。

        Args:
            opt_account_id: 期权账户 ID
            ft_account_id: 期货账户 ID
            balance: 划转金额（元）

        Returns:
            划转结果
        """
        return self._post("/api/fund/ctp_option_to_future", {
            "opt_account_id": opt_account_id,
            "ft_account_id": ft_account_id,
            "balance": balance,
        })

    def ctp_transfer_future_to_option(
        self, opt_account_id: str, ft_account_id: str, balance: float
    ) -> dict:
        """从期货账户划转资金到期权账户（跨市场划转）。

        Args:
            opt_account_id: 期权账户 ID
            ft_account_id: 期货账户 ID
            balance: 划转金额（元）

        Returns:
            划转结果
        """
        return self._post("/api/fund/ctp_future_to_option", {
            "opt_account_id": opt_account_id,
            "ft_account_id": ft_account_id,
            "balance": balance,
        })

    def secu_transfer(
        self,
        transfer_direction: int,
        stock_code: str,
        volume: int,
        transfer_type: int,
        account_id: str = "",
    ) -> dict:
        """证券划转。

        Args:
            transfer_direction: 划转方向
            stock_code: 股票代码
            volume: 划转数量
            transfer_type: 划转类型
            account_id: 交易账户 ID

        Returns:
            划转结果
        """
        return self._post("/api/fund/secu_transfer", {
            "transfer_direction": transfer_direction,
            "stock_code": stock_code,
            "volume": volume,
            "transfer_type": transfer_type,
            "account_id": account_id,
        })

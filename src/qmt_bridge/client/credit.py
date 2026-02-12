"""CreditMixin — 两融（融资融券）交易客户端方法。

对齐 xttrader 真实信用交易 API：
- credit_order — 信用下单（通过 order_type 常量区分融资/融券）
- query_credit_positions — 查询信用持仓
- query_credit_detail — 查询信用账户资产详情
- query_stk_compacts — 查询信用负债合约
- query_credit_slo_code — 查询融券标的
- query_credit_subjects — 查询标的证券
- query_credit_assure — 查询担保品

底层对应 xtquant 的 ``XtQuantTrader`` 类的信用交易方法。
"""


class CreditMixin:
    """两融交易客户端方法集合，对应 /api/credit/* 端点。"""

    def credit_order(
        self,
        stock_code: str,
        order_type: int,
        order_volume: int,
        price_type: int = 5,
        price: float = 0.0,
        strategy_name: str = "",
        order_remark: str = "",
        account_id: str = "",
    ) -> dict:
        """提交两融委托。

        通过 order_type 常量区分融资买入/融券卖出等操作类型。

        Args:
            stock_code: 股票代码
            order_type: 委托类型
            order_volume: 委托数量（股）
            price_type: 报价类型
            price: 委托价格
            strategy_name: 策略名称
            order_remark: 委托备注
            account_id: 交易账户 ID

        Returns:
            委托结果
        """
        return self._post("/api/credit/order", {
            "stock_code": stock_code,
            "order_type": order_type,
            "order_volume": order_volume,
            "price_type": price_type,
            "price": price,
            "strategy_name": strategy_name,
            "order_remark": order_remark,
            "account_id": account_id,
        })

    def query_credit_positions(self, account_id: str = "") -> dict:
        """查询信用账户持仓。

        Args:
            account_id: 交易账户 ID

        Returns:
            信用账户持仓列表
        """
        return self._get("/api/credit/positions", {"account_id": account_id})

    def query_credit_detail(self, account_id: str = "") -> dict:
        """查询信用账户资产详情。

        Args:
            account_id: 交易账户 ID

        Returns:
            信用账户资产详情
        """
        return self._get("/api/credit/asset", {"account_id": account_id})

    def query_stk_compacts(self, account_id: str = "") -> dict:
        """查询信用负债合约。

        Args:
            account_id: 交易账户 ID

        Returns:
            负债合约列表
        """
        return self._get("/api/credit/debt", {"account_id": account_id})

    def query_credit_slo_code(self, account_id: str = "") -> dict:
        """查询融券标的列表。

        Args:
            account_id: 交易账户 ID

        Returns:
            可融券标的列表
        """
        return self._get("/api/credit/slo_stocks", {"account_id": account_id})

    def query_credit_subjects(self, account_id: str = "") -> dict:
        """查询两融标的证券列表。

        Args:
            account_id: 交易账户 ID

        Returns:
            标的证券列表
        """
        return self._get("/api/credit/subjects", {"account_id": account_id})

    def query_credit_assure(self, account_id: str = "") -> dict:
        """查询担保品信息。

        Args:
            account_id: 交易账户 ID

        Returns:
            担保品信息列表
        """
        return self._get("/api/credit/assure", {"account_id": account_id})

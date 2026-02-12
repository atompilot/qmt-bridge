"""TradingMixin — 交易操作客户端方法（需要 API Key 认证）。

对齐 xttrader 真实交易 API，修复参数传递链路。

委托类型 (order_type) 常用值:
    - 23: 买入
    - 24: 卖出

报价类型 (price_type) 常用值:
    - 5:  最新价
    - 11: 限价
    - 42: 最优五档即时成交剩余撤销
"""


class TradingMixin:
    """交易操作客户端方法集合，对应 /api/trading/* 端点。"""

    def place_order(
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
        """委托下单。

        Args:
            stock_code: 股票代码，如 ``"000001.SZ"``
            order_type: 委托类型 — 23=买入, 24=卖出
            order_volume: 委托数量（股）
            price_type: 报价类型
            price: 委托价格
            strategy_name: 策略名称
            order_remark: 委托备注
            account_id: 交易账户 ID

        Returns:
            包含 ``order_id`` 等委托结果的字典
        """
        return self._post("/api/trading/order", {
            "stock_code": stock_code,
            "order_type": order_type,
            "order_volume": order_volume,
            "price_type": price_type,
            "price": price,
            "strategy_name": strategy_name,
            "order_remark": order_remark,
            "account_id": account_id,
        })

    def cancel_order(self, order_id: int, account_id: str = "") -> dict:
        """撤销委托。

        Args:
            order_id: 要撤销的委托 ID
            account_id: 交易账户 ID

        Returns:
            撤单结果
        """
        return self._post("/api/trading/cancel", {
            "order_id": order_id,
            "account_id": account_id,
        })

    def cancel_order_by_sysid(
        self, market: int, sysid: str, account_id: str = ""
    ) -> dict:
        """按系统编号撤单。

        Args:
            market: 市场代码
            sysid: 系统编号
            account_id: 交易账户 ID

        Returns:
            撤单结果
        """
        return self._post("/api/trading/cancel_by_sysid", {
            "market": market,
            "sysid": sysid,
            "account_id": account_id,
        })

    def cancel_order_by_sysid_async(
        self, market: int, sysid: str, account_id: str = ""
    ) -> dict:
        """按系统编号异步撤单（结果通过 WebSocket 回调返回）。

        Args:
            market: 市场代码
            sysid: 系统编号
            account_id: 交易账户 ID

        Returns:
            包含请求序号的字典
        """
        return self._post("/api/trading/cancel_by_sysid_async", {
            "market": market,
            "sysid": sysid,
            "account_id": account_id,
        })

    def query_orders(self, account_id: str = "", cancelable_only: bool = False) -> dict:
        """查询当日委托列表。

        Args:
            account_id: 交易账户 ID
            cancelable_only: 仅返回可撤委托

        Returns:
            委托列表数据
        """
        return self._get("/api/trading/orders", {
            "account_id": account_id,
            "cancelable_only": cancelable_only,
        })

    def query_positions(self, account_id: str = "") -> dict:
        """查询当前持仓列表。

        Args:
            account_id: 交易账户 ID

        Returns:
            持仓列表数据
        """
        return self._get("/api/trading/positions", {"account_id": account_id})

    def query_asset(self, account_id: str = "") -> dict:
        """查询账户资产信息。

        Args:
            account_id: 交易账户 ID

        Returns:
            账户资产信息字典
        """
        return self._get("/api/trading/asset", {"account_id": account_id})

    def query_trades(self, account_id: str = "") -> dict:
        """查询当日成交记录。

        Args:
            account_id: 交易账户 ID

        Returns:
            成交记录列表数据
        """
        return self._get("/api/trading/trades", {"account_id": account_id})

    def query_order_detail(self, order_id: int, account_id: str = "") -> dict:
        """查询指定委托的详细信息。

        Args:
            order_id: 委托 ID
            account_id: 交易账户 ID

        Returns:
            委托详情字典
        """
        return self._get("/api/trading/order_detail", {
            "order_id": order_id,
            "account_id": account_id,
        })

    def batch_order(self, orders: list[dict]) -> dict:
        """批量下单。

        Args:
            orders: 委托列表，每个元素的结构与 ``place_order()`` 的参数相同

        Returns:
            批量下单结果
        """
        return self._post("/api/trading/batch_order", orders)

    def batch_cancel(self, cancel_requests: list[dict]) -> dict:
        """批量撤单。

        Args:
            cancel_requests: 撤单请求列表

        Returns:
            批量撤单结果
        """
        return self._post("/api/trading/batch_cancel", cancel_requests)

    def get_account_status(self, account_id: str = "") -> dict:
        """获取交易账户连接状态。

        Args:
            account_id: 交易账户 ID

        Returns:
            连接状态信息
        """
        return self._get("/api/trading/account_status", {"account_id": account_id})

    def query_account_status_detail(self) -> dict:
        """查询账户状态详情。

        Returns:
            账户状态详情
        """
        return self._get("/api/trading/account_status_detail")

    def query_secu_account(self, account_id: str = "") -> dict:
        """查询证券子账户。

        Args:
            account_id: 交易账户 ID

        Returns:
            证券子账户信息
        """
        return self._get("/api/trading/secu_account", {"account_id": account_id})

    # ------------------------------------------------------------------
    # 异步委托/撤单
    # ------------------------------------------------------------------

    def place_order_async(
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
        """异步委托下单（结果通过 WebSocket 回调返回）。

        参数含义与 ``place_order()`` 相同。

        Returns:
            包含请求序号的字典
        """
        return self._post("/api/trading/order_async", {
            "stock_code": stock_code,
            "order_type": order_type,
            "order_volume": order_volume,
            "price_type": price_type,
            "price": price,
            "strategy_name": strategy_name,
            "order_remark": order_remark,
            "account_id": account_id,
        })

    def cancel_order_async(self, order_id: int, account_id: str = "") -> dict:
        """异步撤单（结果通过 WebSocket 回调返回）。

        Args:
            order_id: 要撤销的委托 ID
            account_id: 交易账户 ID

        Returns:
            包含请求序号的字典
        """
        return self._post("/api/trading/cancel_async", {
            "order_id": order_id,
            "account_id": account_id,
        })

    # ------------------------------------------------------------------
    # 单条查询
    # ------------------------------------------------------------------

    def query_single_order(self, order_id: int, account_id: str = "") -> dict:
        """查询单笔委托。

        Args:
            order_id: 委托 ID
            account_id: 交易账户 ID

        Returns:
            委托信息字典
        """
        return self._get(f"/api/trading/order/{order_id}", {"account_id": account_id})

    def query_single_trade(self, trade_id: int, account_id: str = "") -> dict:
        """查询单笔成交。

        Args:
            trade_id: 成交 ID
            account_id: 交易账户 ID

        Returns:
            成交信息字典
        """
        return self._get(f"/api/trading/trade/{trade_id}", {"account_id": account_id})

    def query_single_position(self, stock_code: str, account_id: str = "") -> dict:
        """查询单只股票的持仓。

        Args:
            stock_code: 股票代码
            account_id: 交易账户 ID

        Returns:
            单只股票持仓信息字典
        """
        return self._get(f"/api/trading/position/{stock_code}", {"account_id": account_id})

    # ------------------------------------------------------------------
    # 新股申购
    # ------------------------------------------------------------------

    def query_new_purchase_limit(self, account_id: str = "") -> dict:
        """查询新股申购额度。

        Args:
            account_id: 交易账户 ID

        Returns:
            申购额度信息
        """
        return self._get("/api/trading/new_purchase_limit", {"account_id": account_id})

    def query_ipo_data(self) -> dict:
        """查询当前 IPO 日历数据。

        Returns:
            IPO 日历数据
        """
        return self._get("/api/trading/ipo_data")

    # ------------------------------------------------------------------
    # 多账户信息
    # ------------------------------------------------------------------

    def query_account_infos(self) -> dict:
        """查询所有已注册交易账户的信息。

        Returns:
            全部交易账户信息字典
        """
        return self._get("/api/trading/account_infos")

    # ------------------------------------------------------------------
    # COM 查询（期权/期货专用账户）
    # ------------------------------------------------------------------

    def query_com_fund(self, account_id: str = "") -> dict:
        """查询 COM 账户资金（期权/期货账户）。

        Args:
            account_id: 交易账户 ID

        Returns:
            COM 账户资金信息
        """
        return self._get("/api/trading/com_fund", {"account_id": account_id})

    def query_com_position(self, account_id: str = "") -> dict:
        """查询 COM 账户持仓（期权/期货账户）。

        Args:
            account_id: 交易账户 ID

        Returns:
            COM 账户持仓信息
        """
        return self._get("/api/trading/com_position", {"account_id": account_id})

    # ------------------------------------------------------------------
    # 数据导出 / 外部同步（对齐 xttrader 真实签名）
    # ------------------------------------------------------------------

    def export_data(
        self,
        result_path: str,
        data_type: str = "",
        start_time: str = "",
        end_time: str = "",
        user_param: str = "",
        account_id: str = "",
    ) -> dict:
        """导出交易数据到文件。

        Args:
            result_path: 导出文件路径
            data_type: 数据类型
            start_time: 开始时间
            end_time: 结束时间
            user_param: 用户自定义参数
            account_id: 交易账户 ID

        Returns:
            导出结果
        """
        return self._post("/api/trading/export_data", {
            "result_path": result_path,
            "data_type": data_type,
            "start_time": start_time,
            "end_time": end_time,
            "user_param": user_param,
            "account_id": account_id,
        })

    def query_data(
        self,
        result_path: str,
        data_type: str = "",
        start_time: str = "",
        end_time: str = "",
        user_param: str = "",
        account_id: str = "",
    ) -> dict:
        """查询已导出的交易数据。

        Args:
            result_path: 结果文件路径
            data_type: 数据类型
            start_time: 开始时间
            end_time: 结束时间
            user_param: 用户自定义参数
            account_id: 交易账户 ID

        Returns:
            查询结果
        """
        return self._post("/api/trading/query_data", {
            "result_path": result_path,
            "data_type": data_type,
            "start_time": start_time,
            "end_time": end_time,
            "user_param": user_param,
            "account_id": account_id,
        })

    def sync_transaction_from_external(
        self,
        operation: str,
        data_type: str,
        deal_list: list[dict],
        account_id: str = "",
    ) -> dict:
        """从外部系统同步成交记录。

        Args:
            operation: 操作类型
            data_type: 数据类型
            deal_list: 成交记录列表
            account_id: 交易账户 ID

        Returns:
            同步结果
        """
        return self._post("/api/trading/sync_transaction", {
            "operation": operation,
            "data_type": data_type,
            "deal_list": deal_list,
            "account_id": account_id,
        })

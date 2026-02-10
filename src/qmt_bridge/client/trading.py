"""TradingMixin — trading client methods (requires API Key)."""


class TradingMixin:
    """Client methods for /api/trading/* endpoints."""

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
            order_type: 委托类型，23=买入, 24=卖出
            order_volume: 委托数量（股）
            price_type: 报价类型，5=最新价, 11=限价等
            price: 委托价格（限价时必填）
            strategy_name: 策略名称（可选）
            order_remark: 委托备注（可选）
            account_id: 交易账户 ID（多账户时指定）

        Returns:
            dict — 包含 order_id 等委托结果
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
            account_id: 交易账户 ID（多账户时指定）
        """
        return self._post("/api/trading/cancel", {
            "order_id": order_id,
            "account_id": account_id,
        })

    def query_orders(self, account_id: str = "", cancelable_only: bool = False) -> dict:
        """查询当日委托列表。

        Args:
            account_id: 交易账户 ID（多账户时指定）
            cancelable_only: 仅返回可撤委托
        """
        return self._get("/api/trading/orders", {
            "account_id": account_id,
            "cancelable_only": cancelable_only,
        })

    def query_positions(self, account_id: str = "") -> dict:
        """Query current positions."""
        return self._get("/api/trading/positions", {"account_id": account_id})

    def query_asset(self, account_id: str = "") -> dict:
        """Query account asset information."""
        return self._get("/api/trading/asset", {"account_id": account_id})

    def query_trades(self, account_id: str = "") -> dict:
        """Query trade records."""
        return self._get("/api/trading/trades", {"account_id": account_id})

    def query_order_detail(self, order_id: int, account_id: str = "") -> dict:
        """Query details for a specific order."""
        return self._get("/api/trading/order_detail", {
            "order_id": order_id,
            "account_id": account_id,
        })

    def batch_order(self, orders: list[dict]) -> dict:
        """Place multiple orders at once."""
        return self._post("/api/trading/batch_order", orders)

    def batch_cancel(self, cancel_requests: list[dict]) -> dict:
        """Cancel multiple orders at once."""
        return self._post("/api/trading/batch_cancel", cancel_requests)

    def get_account_status(self, account_id: str = "") -> dict:
        """Get trading account connection status."""
        return self._get("/api/trading/account_status", {"account_id": account_id})

    def get_account_info(self, account_id: str = "") -> dict:
        """Get trading account basic information."""
        return self._get("/api/trading/account_info", {"account_id": account_id})

    # ------------------------------------------------------------------
    # Async order/cancel
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
        """Place an order asynchronously (result via WebSocket callback)."""
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
        """Cancel an order asynchronously (result via WebSocket callback)."""
        return self._post("/api/trading/cancel_async", {
            "order_id": order_id,
            "account_id": account_id,
        })

    # ------------------------------------------------------------------
    # Single-item queries
    # ------------------------------------------------------------------

    def query_single_order(self, order_id: int, account_id: str = "") -> dict:
        """Query a single order by order_id."""
        return self._get(f"/api/trading/order/{order_id}", {"account_id": account_id})

    def query_single_trade(self, trade_id: int, account_id: str = "") -> dict:
        """Query a single trade by trade_id."""
        return self._get(f"/api/trading/trade/{trade_id}", {"account_id": account_id})

    def query_single_position(self, stock_code: str, account_id: str = "") -> dict:
        """Query position for a single stock."""
        return self._get(f"/api/trading/position/{stock_code}", {"account_id": account_id})

    # ------------------------------------------------------------------
    # Position statistics
    # ------------------------------------------------------------------

    def query_position_statistics(self, account_id: str = "") -> dict:
        """Query position statistics summary."""
        return self._get("/api/trading/position_statistics", {"account_id": account_id})

    # ------------------------------------------------------------------
    # IPO queries
    # ------------------------------------------------------------------

    def query_new_purchase_limit(self, account_id: str = "") -> dict:
        """Query IPO new purchase limit."""
        return self._get("/api/trading/new_purchase_limit", {"account_id": account_id})

    def query_ipo_data(self) -> dict:
        """Query IPO calendar data."""
        return self._get("/api/trading/ipo_data")

    # ------------------------------------------------------------------
    # Account infos (all accounts)
    # ------------------------------------------------------------------

    def query_account_infos(self) -> dict:
        """Query info for all registered trading accounts."""
        return self._get("/api/trading/account_infos")

    # ------------------------------------------------------------------
    # COM queries (期权/期货)
    # ------------------------------------------------------------------

    def query_com_fund(self, account_id: str = "") -> dict:
        """Query COM fund (option/future account funds)."""
        return self._get("/api/trading/com_fund", {"account_id": account_id})

    def query_com_position(self, account_id: str = "") -> dict:
        """Query COM positions (option/future account positions)."""
        return self._get("/api/trading/com_position", {"account_id": account_id})

    # ------------------------------------------------------------------
    # Data export / external sync
    # ------------------------------------------------------------------

    def export_data(
        self, data_type: str = "orders", file_path: str = "", account_id: str = ""
    ) -> dict:
        """Export trading data to file."""
        return self._post("/api/trading/export_data", {
            "data_type": data_type,
            "file_path": file_path,
            "account_id": account_id,
        })

    def query_data(self, data_type: str = "orders", account_id: str = "") -> dict:
        """Query exported trading data."""
        return self._get("/api/trading/query_data", {
            "data_type": data_type,
            "account_id": account_id,
        })

    def sync_transaction_from_external(
        self, data: list[dict], account_id: str = ""
    ) -> dict:
        """Sync external transaction records into the system."""
        return self._post("/api/trading/sync_transaction", {
            "data": data,
            "account_id": account_id,
        })

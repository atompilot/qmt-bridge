"""SMTMixin — SMT (约定式交易) client methods."""


class SMTMixin:
    """Client methods for /api/smt/* endpoints."""

    def smt_order(
        self,
        stock_code: str,
        order_type: int,
        order_volume: int,
        price_type: int = 5,
        price: float = 0.0,
        smt_type: str = "",
        strategy_name: str = "",
        order_remark: str = "",
        account_id: str = "",
    ) -> dict:
        """Place an SMT order."""
        return self._post("/api/smt/order", {
            "stock_code": stock_code,
            "order_type": order_type,
            "order_volume": order_volume,
            "price_type": price_type,
            "price": price,
            "smt_type": smt_type,
            "strategy_name": strategy_name,
            "order_remark": order_remark,
            "account_id": account_id,
        })

    def smt_negotiate_order_async(
        self,
        stock_code: str,
        order_type: int,
        order_volume: int,
        price: float = 0.0,
        compact_id: str = "",
        strategy_name: str = "",
        order_remark: str = "",
        account_id: str = "",
    ) -> dict:
        """Place an SMT negotiate order asynchronously (result via WebSocket callback)."""
        return self._post("/api/smt/negotiate_order_async", {
            "stock_code": stock_code,
            "order_type": order_type,
            "order_volume": order_volume,
            "price": price,
            "compact_id": compact_id,
            "strategy_name": strategy_name,
            "order_remark": order_remark,
            "account_id": account_id,
        })

    def cancel_smt_order(self, order_id: int, account_id: str = "") -> dict:
        """Cancel an SMT order."""
        return self._post("/api/smt/cancel", {
            "order_id": order_id,
            "account_id": account_id,
        })

    def smt_query_quoter(self, account_id: str = "") -> dict:
        """Query SMT quoter information (报价方信息)."""
        return self._get("/api/smt/quoter", {"account_id": account_id})

    def smt_query_compact(self, account_id: str = "") -> dict:
        """Query SMT compacts (约定合约)."""
        return self._get("/api/smt/compact", {"account_id": account_id})

    def query_appointment_info(self, account_id: str = "") -> dict:
        """Query SMT appointment info (约定式预约信息)."""
        return self._get("/api/smt/appointment", {"account_id": account_id})

    def query_smt_secu_info(self, account_id: str = "") -> dict:
        """Query SMT security info (约定式证券信息)."""
        return self._get("/api/smt/secu_info", {"account_id": account_id})

    def query_smt_secu_rate(self, account_id: str = "") -> dict:
        """Query SMT security rates (约定式证券费率)."""
        return self._get("/api/smt/secu_rate", {"account_id": account_id})

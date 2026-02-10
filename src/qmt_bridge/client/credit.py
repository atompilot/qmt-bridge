"""CreditMixin — credit (margin) trading client methods."""


class CreditMixin:
    """Client methods for /api/credit/* endpoints."""

    def credit_order(
        self,
        stock_code: str,
        order_type: int,
        order_volume: int,
        price_type: int = 5,
        price: float = 0.0,
        credit_type: str = "fin_buy",
        strategy_name: str = "",
        order_remark: str = "",
        account_id: str = "",
    ) -> dict:
        """Place a credit (margin) trading order."""
        return self._post("/api/credit/order", {
            "stock_code": stock_code,
            "order_type": order_type,
            "order_volume": order_volume,
            "price_type": price_type,
            "price": price,
            "credit_type": credit_type,
            "strategy_name": strategy_name,
            "order_remark": order_remark,
            "account_id": account_id,
        })

    def query_credit_positions(self, account_id: str = "") -> dict:
        """Query credit trading positions."""
        return self._get("/api/credit/positions", {"account_id": account_id})

    def query_credit_asset(self, account_id: str = "") -> dict:
        """Query credit trading account asset."""
        return self._get("/api/credit/asset", {"account_id": account_id})

    def query_credit_debt(self, account_id: str = "") -> dict:
        """Query credit debt information."""
        return self._get("/api/credit/debt", {"account_id": account_id})

    def query_credit_available(self, stock_code: str = "", account_id: str = "") -> dict:
        """Query available credit amount for a stock."""
        return self._get("/api/credit/available_amount", {
            "stock_code": stock_code,
            "account_id": account_id,
        })

    def query_slo_stocks(self, account_id: str = "") -> dict:
        """Query stocks available for short selling."""
        return self._get("/api/credit/slo_stocks", {"account_id": account_id})

    def query_fin_stocks(self, account_id: str = "") -> dict:
        """Query stocks available for margin buying."""
        return self._get("/api/credit/fin_stocks", {"account_id": account_id})

    def query_credit_subjects(self, account_id: str = "") -> dict:
        """Query credit subject list (标的证券)."""
        return self._get("/api/credit/subjects", {"account_id": account_id})

    def query_credit_assure(self, account_id: str = "") -> dict:
        """Query credit assurance / collateral info (担保品)."""
        return self._get("/api/credit/assure", {"account_id": account_id})

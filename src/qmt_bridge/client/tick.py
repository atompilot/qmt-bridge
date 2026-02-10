"""TickMixin — L2/tick data client methods."""


class TickMixin:
    """Client methods for /api/tick/* endpoints."""

    def get_l2_quote(
        self, stock: str, start_time: str = "", end_time: str = "", count: int = -1
    ) -> dict:
        """Fetch L2 quote snapshot."""
        resp = self._get("/api/tick/l2_quote", {
            "stock": stock,
            "start_time": start_time,
            "end_time": end_time,
            "count": count,
        })
        return resp.get("data", {})

    def get_l2_order(
        self, stock: str, start_time: str = "", end_time: str = "", count: int = -1
    ) -> dict:
        """Fetch L2 order-by-order data."""
        resp = self._get("/api/tick/l2_order", {
            "stock": stock,
            "start_time": start_time,
            "end_time": end_time,
            "count": count,
        })
        return resp.get("data", {})

    def get_l2_transaction(
        self, stock: str, start_time: str = "", end_time: str = "", count: int = -1
    ) -> dict:
        """Fetch L2 transaction-by-transaction data."""
        resp = self._get("/api/tick/l2_transaction", {
            "stock": stock,
            "start_time": start_time,
            "end_time": end_time,
            "count": count,
        })
        return resp.get("data", {})

    def get_l2_thousand_quote(
        self, stock: str, start_time: str = "", end_time: str = "", count: int = -1
    ) -> dict:
        """Fetch L2 thousand-level quote."""
        resp = self._get("/api/tick/l2_thousand_quote", {
            "stock": stock,
            "start_time": start_time,
            "end_time": end_time,
            "count": count,
        })
        return resp.get("data", {})

    def get_l2_thousand_orderbook(
        self, stock: str, start_time: str = "", end_time: str = "", count: int = -1
    ) -> dict:
        """Fetch L2 thousand-level order book."""
        resp = self._get("/api/tick/l2_thousand_orderbook", {
            "stock": stock,
            "start_time": start_time,
            "end_time": end_time,
            "count": count,
        })
        return resp.get("data", {})

    def get_l2_thousand_trade(
        self, stock: str, start_time: str = "", end_time: str = "", count: int = -1
    ) -> dict:
        """Fetch L2 thousand-level trade data."""
        resp = self._get("/api/tick/l2_thousand_trade", {
            "stock": stock,
            "start_time": start_time,
            "end_time": end_time,
            "count": count,
        })
        return resp.get("data", {})

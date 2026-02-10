"""MetaMixin — system metadata client methods."""


class MetaMixin:
    """Client methods for /api/meta/* endpoints."""

    def get_markets(self) -> dict:
        """Fetch available markets."""
        resp = self._get("/api/meta/markets")
        return resp.get("markets", {})

    def get_periods(self) -> list:
        """Fetch available K-line periods."""
        resp = self._get("/api/meta/periods")
        return resp.get("periods", [])

    def get_stock_list_by_category(self, category: str) -> list[str]:
        """Fetch stock codes by category."""
        resp = self._get("/api/meta/stock_list", {"category": category})
        return resp.get("stocks", [])

    def get_last_trade_date(self, market: str) -> str:
        """Fetch the last trade date for a market."""
        resp = self._get("/api/meta/last_trade_date", {"market": market})
        return resp.get("last_trade_date", "")

    def get_server_version(self) -> str:
        """Fetch the QMT Bridge server version."""
        resp = self._get("/api/meta/version")
        return resp.get("version", "")

    def get_xtdata_version(self) -> str:
        """Fetch xtquant/xtdata library version on the server."""
        resp = self._get("/api/meta/xtdata_version")
        return resp.get("xtdata_version", "")

    def get_connection_status(self) -> dict:
        """Check xtdata connection status."""
        return self._get("/api/meta/connection_status")

    def health_check(self) -> dict:
        """Simple health check."""
        return self._get("/api/meta/health")

    def get_quote_server_status(self) -> dict:
        """Get detailed quote server connection status."""
        return self._get("/api/meta/quote_server_status")

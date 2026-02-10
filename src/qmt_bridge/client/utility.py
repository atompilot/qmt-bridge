"""UtilityMixin — utility client methods."""


class UtilityMixin:
    """Client methods for /api/utility/* endpoints."""

    def get_stock_name(self, stock: str) -> str:
        """Get the Chinese name for a stock code."""
        resp = self._get("/api/utility/stock_name", {"stock": stock})
        return resp.get("name", "")

    def get_batch_stock_name(self, stocks: list[str]) -> dict[str, str]:
        """Get Chinese names for multiple stock codes."""
        resp = self._get("/api/utility/batch_stock_name", {"stocks": ",".join(stocks)})
        return resp.get("data", {})

    def code_to_market(self, stock: str) -> dict:
        """Determine which market a stock code belongs to."""
        return self._get("/api/utility/code_to_market", {"stock": stock})

    def search_stocks(
        self, keyword: str, category: str = "沪深A股", limit: int = 20
    ) -> list[str]:
        """Search stocks by keyword (code prefix or name)."""
        resp = self._get("/api/utility/search", {
            "keyword": keyword,
            "category": category,
            "limit": limit,
        })
        return resp.get("stocks", [])

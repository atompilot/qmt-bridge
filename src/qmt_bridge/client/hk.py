"""HKMixin — Hong Kong market client methods."""


class HKMixin:
    """Client methods for /api/hk/* endpoints."""

    def get_hk_stock_list(self) -> list[str]:
        """Get list of HK-connected stocks."""
        resp = self._get("/api/hk/stock_list")
        return resp.get("stocks", [])

    def get_hk_connect_stocks(self, connect_type: str = "north") -> list[str]:
        """Get HK-connect stock list by direction."""
        resp = self._get("/api/hk/connect_stocks", {"connect_type": connect_type})
        return resp.get("stocks", [])

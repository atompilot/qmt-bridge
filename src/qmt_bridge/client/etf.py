"""ETFMixin — ETF & convertible bond client methods."""


class ETFMixin:
    """Client methods for /api/etf/* and /api/cb/* endpoints."""

    def get_etf_list(self) -> list[str]:
        """Fetch lightweight ETF code list."""
        resp = self._get("/api/etf/list")
        return resp.get("stocks", [])

    def get_etf_info(self) -> dict:
        """Fetch ETF subscription/redemption list."""
        resp = self._get("/api/etf/info")
        return resp.get("data", {})

    def get_cb_info(self, stock: str) -> dict:
        """Fetch convertible bond information."""
        resp = self._get("/api/cb/info", {"stock": stock})
        return resp.get("data", {})

    def get_cb_list(self) -> list[str]:
        """Fetch all convertible bond codes."""
        resp = self._get("/api/cb/list")
        return resp.get("stocks", [])

    def get_cb_detail(self, stock: str) -> dict:
        """Fetch detailed convertible bond information."""
        resp = self._get("/api/cb/detail", {"stock": stock})
        return resp.get("data", {})

    def get_cb_conversion_price(self, stock: str) -> dict:
        """Fetch convertible bond conversion price info."""
        resp = self._get("/api/cb/conversion_price", {"stock": stock})
        return resp.get("data", {})

    def get_bond_info(self, stock: str) -> dict:
        """Fetch bond-specific information."""
        resp = self._get("/api/cb/bond_info", {"stock": stock})
        return resp.get("data", {})

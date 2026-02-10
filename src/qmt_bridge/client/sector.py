"""SectorMixin — sector data client methods."""


class SectorMixin:
    """Client methods for /api/sector/* endpoints."""

    def get_sector_list(self) -> list[str]:
        """Fetch all available sector names."""
        resp = self._get("/api/sector/list")
        return resp.get("sectors", [])

    def get_sector_info(self, sector: str = "") -> dict:
        """Fetch sector metadata."""
        resp = self._get("/api/sector/info", {"sector": sector})
        return resp.get("data", {})

    def get_sector_stocks(self, sector: str) -> list[str]:
        """Fetch all stock codes in a given sector (legacy)."""
        resp = self._get("/api/sector_stocks", {"sector": sector})
        return resp.get("stocks", [])

    def get_sector_stocks_v2(
        self, sector: str, real_timetag: int = -1
    ) -> list[str]:
        """Fetch stock codes in a sector (supports historical composition)."""
        resp = self._get("/api/sector/stocks", {
            "sector": sector,
            "real_timetag": real_timetag,
        })
        return resp.get("stocks", [])

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def create_sector_folder(self, folder_name: str) -> dict:
        """Create a new sector folder."""
        return self._post("/api/sector/create_folder", {"folder_name": folder_name})

    def create_sector(self, sector_name: str, parent_node: str = "") -> dict:
        """Create a new sector."""
        return self._post("/api/sector/create", {
            "sector_name": sector_name,
            "parent_node": parent_node,
        })

    def add_sector_stocks(self, sector_name: str, stocks: list[str]) -> dict:
        """Add stocks to a sector."""
        return self._post("/api/sector/add_stocks", {
            "sector_name": sector_name,
            "stocks": stocks,
        })

    def remove_sector_stocks(self, sector_name: str, stocks: list[str]) -> dict:
        """Remove stocks from a sector."""
        return self._post("/api/sector/remove_stocks", {
            "sector_name": sector_name,
            "stocks": stocks,
        })

    def remove_sector(self, sector_name: str) -> dict:
        """Remove an entire sector."""
        return self._delete("/api/sector/remove", {"sector_name": sector_name})

    def reset_sector(self, sector_name: str, stocks: list[str]) -> dict:
        """Reset sector stocks (replace all stocks)."""
        return self._post("/api/sector/reset", {
            "sector_name": sector_name,
            "stocks": stocks,
        })

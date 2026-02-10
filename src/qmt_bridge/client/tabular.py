"""TabularMixin — tabular data client methods."""


class TabularMixin:
    """Client methods for /api/tabular/* endpoints."""

    def get_tabular_data(
        self,
        table_name: str,
        stocks: list[str] | None = None,
        start_time: str = "",
        end_time: str = "",
    ) -> dict:
        """Get data from a named tabular data source."""
        resp = self._get("/api/tabular/data", {
            "table_name": table_name,
            "stocks": ",".join(stocks) if stocks else "",
            "start_time": start_time,
            "end_time": end_time,
        })
        return resp.get("data", {})

    def list_tables(self) -> list:
        """List available tabular data tables."""
        resp = self._get("/api/tabular/tables")
        return resp.get("tables", [])

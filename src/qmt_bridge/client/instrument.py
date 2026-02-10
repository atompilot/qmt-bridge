"""InstrumentMixin — instrument info client methods."""


class InstrumentMixin:
    """Client methods for /api/instrument/* endpoints."""

    def get_batch_instrument_detail(
        self, stocks: list[str], iscomplete: bool = False
    ) -> dict:
        """Fetch instrument details for multiple stocks."""
        resp = self._get("/api/instrument/batch_detail", {
            "stocks": ",".join(stocks),
            "iscomplete": iscomplete,
        })
        return resp.get("data", {})

    def get_instrument_type(self, stock: str) -> str:
        """Determine instrument type (stock/futures/option/...)."""
        resp = self._get("/api/instrument/type", {"stock": stock})
        return resp.get("type", "")

    def get_ipo_info(self, start_time: str = "", end_time: str = "") -> dict:
        """Fetch IPO information."""
        resp = self._get("/api/instrument/ipo_info", {
            "start_time": start_time,
            "end_time": end_time,
        })
        return resp.get("data", {})

    def get_index_weight(self, index_code: str) -> dict:
        """Fetch index constituent weights."""
        resp = self._get("/api/instrument/index_weight", {"index_code": index_code})
        return resp.get("data", {})

    def get_st_history(self, stock: str) -> dict:
        """Fetch ST history for a stock."""
        resp = self._get("/api/instrument/st_history", {"stock": stock})
        return resp.get("data", {})

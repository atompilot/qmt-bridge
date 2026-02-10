"""FuturesMixin — futures data client methods."""


class FuturesMixin:
    """Client methods for /api/futures/* endpoints."""

    def get_main_contract(
        self, code_market: str, start_time: str = "", end_time: str = ""
    ) -> dict:
        """Fetch futures main contract."""
        resp = self._get("/api/futures/main_contract", {
            "code_market": code_market,
            "start_time": start_time,
            "end_time": end_time,
        })
        return resp.get("data", {})

    def get_sec_main_contract(
        self, code_market: str, start_time: str = "", end_time: str = ""
    ) -> dict:
        """Fetch futures secondary main contract."""
        resp = self._get("/api/futures/sec_main_contract", {
            "code_market": code_market,
            "start_time": start_time,
            "end_time": end_time,
        })
        return resp.get("data", {})

"""OptionMixin — option data client methods."""


class OptionMixin:
    """Client methods for /api/option/* endpoints."""

    def get_option_detail(self, option_code: str) -> dict:
        """Fetch option contract details."""
        resp = self._get("/api/option/detail", {"option_code": option_code})
        return resp.get("data", {})

    def get_option_chain(self, undl_code: str) -> dict:
        """Fetch option chain for underlying."""
        resp = self._get("/api/option/chain", {"undl_code": undl_code})
        return resp.get("data", {})

    def get_option_list(
        self,
        undl_code: str,
        dedate: str,
        opttype: str = "",
        isavailable: bool = False,
    ) -> list:
        """Fetch option list filtered by expiry/type."""
        resp = self._get("/api/option/list", {
            "undl_code": undl_code,
            "dedate": dedate,
            "opttype": opttype,
            "isavailable": isavailable,
        })
        return resp.get("data", [])

    def get_history_option_list(self, undl_code: str, dedate: str) -> list:
        """Fetch historical option list."""
        resp = self._get("/api/option/history_list", {
            "undl_code": undl_code,
            "dedate": dedate,
        })
        return resp.get("data", [])

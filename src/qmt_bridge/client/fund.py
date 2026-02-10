"""FundMixin — fund transfer client methods."""


class FundMixin:
    """Client methods for /api/fund/* endpoints."""

    def fund_transfer(
        self, transfer_direction: int, amount: float, account_id: str = ""
    ) -> dict:
        """Transfer funds between accounts."""
        return self._post("/api/fund/transfer", {
            "transfer_direction": transfer_direction,
            "amount": amount,
            "account_id": account_id,
        })

    def query_transfer_records(self, account_id: str = "") -> dict:
        """Query fund transfer records."""
        return self._get("/api/fund/transfer_records", {"account_id": account_id})

    def query_available_fund(self, account_id: str = "") -> dict:
        """Query available fund balance."""
        return self._get("/api/fund/available", {"account_id": account_id})

    def ctp_transfer_in(self, amount: float, account_id: str = "") -> dict:
        """Transfer funds into CTP account."""
        return self._post("/api/fund/ctp_transfer_in", {
            "transfer_direction": 0,
            "amount": amount,
            "account_id": account_id,
        })

    def ctp_transfer_out(self, amount: float, account_id: str = "") -> dict:
        """Transfer funds out of CTP account."""
        return self._post("/api/fund/ctp_transfer_out", {
            "transfer_direction": 1,
            "amount": amount,
            "account_id": account_id,
        })

    def query_ctp_balance(self, account_id: str = "") -> dict:
        """Query CTP account balance."""
        return self._get("/api/fund/ctp_balance", {"account_id": account_id})

    def ctp_transfer_option_to_future(self, amount: float, account_id: str = "") -> dict:
        """Transfer from option account to future account (cross-market)."""
        return self._post("/api/fund/ctp_option_to_future", {
            "amount": amount,
            "account_id": account_id,
        })

    def ctp_transfer_future_to_option(self, amount: float, account_id: str = "") -> dict:
        """Transfer from future account to option account (cross-market)."""
        return self._post("/api/fund/ctp_future_to_option", {
            "amount": amount,
            "account_id": account_id,
        })

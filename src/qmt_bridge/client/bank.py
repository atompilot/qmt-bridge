"""BankMixin — bank transfer client methods."""


class BankMixin:
    """Client methods for /api/bank/* endpoints."""

    def bank_transfer_in(
        self, amount: float, bank_code: str = "", account_id: str = ""
    ) -> dict:
        """Transfer funds from bank to securities account."""
        return self._post("/api/bank/transfer_in", {
            "transfer_direction": 0,
            "amount": amount,
            "bank_code": bank_code,
            "account_id": account_id,
        })

    def bank_transfer_out(
        self, amount: float, bank_code: str = "", account_id: str = ""
    ) -> dict:
        """Transfer funds from securities account to bank."""
        return self._post("/api/bank/transfer_out", {
            "transfer_direction": 1,
            "amount": amount,
            "bank_code": bank_code,
            "account_id": account_id,
        })

    def query_bank_balance(self, account_id: str = "") -> dict:
        """Query bank account balance."""
        return self._get("/api/bank/balance", {"account_id": account_id})

    def query_bank_transfer_records(self, account_id: str = "") -> dict:
        """Query bank transfer records."""
        return self._get("/api/bank/transfer_records", {"account_id": account_id})

    def query_bound_banks(self, account_id: str = "") -> dict:
        """Query bound bank accounts."""
        return self._get("/api/bank/banks", {"account_id": account_id})

    def query_transfer_limit(self, account_id: str = "") -> dict:
        """Query bank transfer limit."""
        return self._get("/api/bank/transfer_limit", {"account_id": account_id})

    def query_bank_available(self, account_id: str = "") -> dict:
        """Query available amount for bank transfer."""
        return self._get("/api/bank/available_amount", {"account_id": account_id})

    def query_bank_transfer_status(
        self, transfer_id: str = "", account_id: str = ""
    ) -> dict:
        """Query status of a specific bank transfer."""
        return self._get("/api/bank/status", {
            "transfer_id": transfer_id,
            "account_id": account_id,
        })

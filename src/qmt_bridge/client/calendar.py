"""CalendarMixin — trading calendar client methods."""


class CalendarMixin:
    """Client methods for /api/calendar/* endpoints."""

    def get_trading_dates(
        self, market: str, start_time: str = "", end_time: str = "", count: int = -1
    ) -> list:
        """Fetch trading dates for a market."""
        resp = self._get("/api/calendar/trading_dates", {
            "market": market,
            "start_time": start_time,
            "end_time": end_time,
            "count": count,
        })
        return resp.get("dates", [])

    def get_holidays(self) -> list:
        """Fetch holiday list."""
        resp = self._get("/api/calendar/holidays")
        return resp.get("holidays", [])

    def get_trading_calendar(
        self, market: str, start_time: str = "", end_time: str = ""
    ) -> list:
        """Fetch complete trading calendar (including future dates)."""
        resp = self._get("/api/calendar/trading_calendar", {
            "market": market,
            "start_time": start_time,
            "end_time": end_time,
        })
        return resp.get("calendar", [])

    def get_trading_period(self, stock: str) -> list:
        """Fetch trading time periods for a stock."""
        resp = self._get("/api/calendar/trading_period", {"stock": stock})
        return resp.get("periods", [])

    def is_trading_date(self, market: str, date: str) -> bool:
        """Check whether a given date is a trading date."""
        resp = self._get("/api/calendar/is_trading_date", {
            "market": market,
            "date": date,
        })
        return resp.get("is_trading", False)

    def get_prev_trading_date(self, market: str, date: str = "") -> str | None:
        """Get the previous trading date."""
        resp = self._get("/api/calendar/prev_trading_date", {
            "market": market,
            "date": date,
        })
        return resp.get("prev_trading_date")

    def get_next_trading_date(self, market: str, date: str = "") -> str | None:
        """Get the next trading date."""
        resp = self._get("/api/calendar/next_trading_date", {
            "market": market,
            "date": date,
        })
        return resp.get("next_trading_date")

    def get_trading_dates_count(
        self, market: str, start_time: str = "", end_time: str = ""
    ) -> int:
        """Count number of trading dates in a range."""
        resp = self._get("/api/calendar/trading_dates_count", {
            "market": market,
            "start_time": start_time,
            "end_time": end_time,
        })
        return resp.get("count", 0)

    def get_trading_time(self, stock: str) -> dict:
        """Get trading time info for a stock."""
        resp = self._get("/api/calendar/trading_time", {"stock": stock})
        return resp.get("trading_time", {})

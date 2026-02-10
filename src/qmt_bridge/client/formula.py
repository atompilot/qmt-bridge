"""FormulaMixin — formula/model API client methods."""


class FormulaMixin:
    """Client methods for /api/formula/* endpoints."""

    def call_formula(
        self,
        formula_name: str,
        stock_code: str,
        period: str = "1d",
        start_time: str = "",
        end_time: str = "",
        count: int = -1,
        dividend_type: str = "none",
        **params,
    ) -> dict:
        """Call a formula/indicator on a single stock."""
        return self._post("/api/formula/call", {
            "formula_name": formula_name,
            "stock_code": stock_code,
            "period": period,
            "start_time": start_time,
            "end_time": end_time,
            "count": count,
            "dividend_type": dividend_type,
            "params": params,
        })

    def call_formula_batch(
        self,
        formula_name: str,
        stock_codes: list[str],
        period: str = "1d",
        start_time: str = "",
        end_time: str = "",
        count: int = -1,
        dividend_type: str = "none",
        **params,
    ) -> dict:
        """Call a formula/indicator on multiple stocks."""
        return self._post("/api/formula/call_batch", {
            "formula_name": formula_name,
            "stock_codes": stock_codes,
            "period": period,
            "start_time": start_time,
            "end_time": end_time,
            "count": count,
            "dividend_type": dividend_type,
            "params": params,
        })

    def generate_index_data(
        self,
        index_code: str,
        stocks: list[str],
        weights: list[float],
        period: str = "1d",
        start_time: str = "",
        end_time: str = "",
    ) -> dict:
        """Generate custom index data from stocks and weights."""
        return self._post("/api/formula/generate_index", {
            "index_code": index_code,
            "stocks": stocks,
            "weights": weights,
            "period": period,
            "start_time": start_time,
            "end_time": end_time,
        })

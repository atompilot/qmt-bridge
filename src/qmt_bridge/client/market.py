"""MarketMixin — market data client methods."""

from typing import Optional


class MarketMixin:
    """Client methods for /api/market/* and legacy market endpoints."""

    # ------------------------------------------------------------------
    # Legacy API
    # ------------------------------------------------------------------

    def get_history(
        self,
        stock: str,
        period: str = "1d",
        count: int = 100,
        fields: str = "open,high,low,close,volume",
    ):
        """获取单只股票的历史 K 线数据。

        Args:
            stock: 股票代码，如 ``"000001.SZ"``
            period: K 线周期，如 ``"1d"`` / ``"1m"`` / ``"5m"`` / ``"1w"``
            count: 返回条数
            fields: 返回字段，逗号分隔

        Returns:
            安装了 pandas 时返回 DataFrame，否则返回 list[dict]
        """
        resp = self._get("/api/history", {
            "stock": stock,
            "period": period,
            "count": count,
            "fields": fields,
        })
        records = resp.get("data", [])
        try:
            import pandas as pd
        except ImportError:
            return records
        if not records:
            return pd.DataFrame()
        df = pd.DataFrame(records)
        if "date" in df.columns:
            df.set_index("date", inplace=True)
        return df

    def get_batch_history(
        self,
        stocks: list[str],
        period: str = "1d",
        count: int = 100,
        fields: str = "open,high,low,close,volume",
    ):
        """批量获取多只股票的历史 K 线数据。

        Args:
            stocks: 股票代码列表，如 ``["000001.SZ", "600519.SH"]``
            period: K 线周期，如 ``"1d"`` / ``"1m"`` / ``"5m"`` / ``"1w"``
            count: 每只股票返回条数
            fields: 返回字段，逗号分隔

        Returns:
            安装了 pandas 时返回 dict[str, DataFrame]，否则返回 dict[str, list[dict]]
        """
        resp = self._get("/api/batch_history", {
            "stocks": ",".join(stocks),
            "period": period,
            "count": count,
            "fields": fields,
        })
        data = resp.get("data", {})
        try:
            import pandas as pd
        except ImportError:
            return data
        result: dict = {}
        for stock, records in data.items():
            if not records:
                result[stock] = pd.DataFrame()
                continue
            df = pd.DataFrame(records)
            if "date" in df.columns:
                df.set_index("date", inplace=True)
            result[stock] = df
        return result

    def get_full_tick(self, stocks: list[str]) -> dict:
        """Fetch latest tick snapshot for given stocks."""
        resp = self._get("/api/full_tick", {"stocks": ",".join(stocks)})
        return resp.get("data", {})

    def get_instrument_detail(self, stock: str) -> dict:
        """Fetch instrument details for a stock (legacy)."""
        resp = self._get("/api/instrument_detail", {"stock": stock})
        return resp.get("detail", {})

    def download(self, stock: str, period: str = "1d", start: str = "", end: str = "") -> dict:
        """Trigger history data download on the server side (legacy)."""
        return self._post("/api/download", {
            "stock": stock,
            "period": period,
            "start": start,
            "end": end,
        })

    # ------------------------------------------------------------------
    # New market API
    # ------------------------------------------------------------------

    def get_history_ex(
        self,
        stocks: list[str],
        period: str = "1d",
        start_time: str = "",
        end_time: str = "",
        count: int = -1,
        dividend_type: str = "none",
        fill_data: bool = True,
    ):
        """获取增强版 K 线数据，支持除权处理和数据填充。

        Args:
            stocks: 股票代码列表，如 ``["000001.SZ", "600519.SH"]``
            period: K 线周期，如 ``"1d"`` / ``"1m"`` / ``"5m"``
            start_time: 开始时间，格式 ``"20230101"`` 或 ``"20230101093000"``
            end_time: 结束时间，格式同上
            count: 返回条数，-1 表示全部
            dividend_type: 除权类型 ``"none"`` / ``"front"`` / ``"back"`` / ``"front_ratio"`` / ``"back_ratio"``
            fill_data: 是否填充停牌等缺失数据

        Returns:
            dict[str, DataFrame]，安装了 pandas 时值为 DataFrame，否则为 list[dict]
        """
        resp = self._get("/api/market/history_ex", {
            "stocks": ",".join(stocks),
            "period": period,
            "start_time": start_time,
            "end_time": end_time,
            "count": count,
            "dividend_type": dividend_type,
            "fill_data": fill_data,
        })
        return self._to_dataframes(resp.get("data", {}))

    def get_local_data(
        self,
        stocks: list[str],
        period: str = "1d",
        start_time: str = "",
        end_time: str = "",
        count: int = -1,
        dividend_type: str = "none",
        fill_data: bool = True,
    ):
        """仅从服务端本地缓存读取数据（离线可用）。

        参数含义与 ``get_history_ex`` 相同，区别在于本方法不会触发网络请求，
        仅读取已下载到本地的数据。

        Args:
            stocks: 股票代码列表
            period: K 线周期
            start_time: 开始时间
            end_time: 结束时间
            count: 返回条数，-1 表示全部
            dividend_type: 除权类型
            fill_data: 是否填充缺失数据
        """
        resp = self._get("/api/market/local_data", {
            "stocks": ",".join(stocks),
            "period": period,
            "start_time": start_time,
            "end_time": end_time,
            "count": count,
            "dividend_type": dividend_type,
            "fill_data": fill_data,
        })
        return self._to_dataframes(resp.get("data", {}))

    def get_market_snapshot(self, stocks: list[str]) -> dict:
        """获取实时行情快照（个股/指数）。

        Args:
            stocks: 股票代码列表，如 ``["000001.SZ", "000001.SH"]``

        Returns:
            dict — 以股票代码为 key 的快照数据
        """
        resp = self._get("/api/market/snapshot", {"stocks": ",".join(stocks)})
        return resp.get("data", {})

    def get_major_indices(self) -> dict:
        """Fetch real-time snapshot of major market indices."""
        return self._get("/api/market/indices")

    def get_divid_factors(
        self, stock: str, start_time: str = "", end_time: str = ""
    ) -> dict:
        """Fetch dividend/split adjustment factors."""
        resp = self._get("/api/market/divid_factors", {
            "stock": stock,
            "start_time": start_time,
            "end_time": end_time,
        })
        return resp.get("data", {})

    def get_market_data(
        self,
        stocks: list[str],
        fields: str = "open,high,low,close,volume",
        period: str = "1d",
        start_time: str = "",
        end_time: str = "",
        count: int = -1,
        dividend_type: str = "none",
        fill_data: bool = True,
    ) -> dict:
        """Get market data via get_market_data API."""
        resp = self._get("/api/market/market_data", {
            "stocks": ",".join(stocks),
            "fields": fields,
            "period": period,
            "start_time": start_time,
            "end_time": end_time,
            "count": count,
            "dividend_type": dividend_type,
            "fill_data": fill_data,
        })
        return resp.get("data", {})

    def get_market_data3(
        self,
        stocks: list[str],
        fields: str = "",
        period: str = "1d",
        start_time: str = "",
        end_time: str = "",
        count: int = -1,
        dividend_type: str = "none",
        fill_data: bool = True,
    ):
        """Get market data via get_market_data3 API."""
        resp = self._get("/api/market/market_data3", {
            "stocks": ",".join(stocks),
            "fields": fields,
            "period": period,
            "start_time": start_time,
            "end_time": end_time,
            "count": count,
            "dividend_type": dividend_type,
            "fill_data": fill_data,
        })
        return self._to_dataframes(resp.get("data", {}))

    def get_full_kline(
        self, stock: str, period: str = "1d", start_time: str = "", end_time: str = ""
    ) -> dict:
        """Get full K-line data for a single stock."""
        resp = self._get("/api/market/full_kline", {
            "stock": stock,
            "period": period,
            "start_time": start_time,
            "end_time": end_time,
        })
        return resp.get("data", {})

    def get_fullspeed_orderbook(
        self, stock: str, start_time: str = "", end_time: str = ""
    ) -> dict:
        """Get full-speed order book data."""
        resp = self._get("/api/market/fullspeed_orderbook", {
            "stock": stock,
            "start_time": start_time,
            "end_time": end_time,
        })
        return resp.get("data", {})

    def get_transactioncount(
        self, stock: str, start_time: str = "", end_time: str = ""
    ) -> dict:
        """Get transaction count data."""
        resp = self._get("/api/market/transactioncount", {
            "stock": stock,
            "start_time": start_time,
            "end_time": end_time,
        })
        return resp.get("data", {})

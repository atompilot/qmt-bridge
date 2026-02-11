"""DownloadMixin — data download client methods."""


class DownloadMixin:
    """Client methods for /api/download/* endpoints."""

    def download_batch(
        self,
        stocks: list[str],
        period: str = "1d",
        start_time: str = "",
        end_time: str = "",
    ) -> dict:
        """触发服务端批量下载历史数据。

        Args:
            stocks: 股票代码列表，如 ``["000001.SZ", "600519.SH"]``
            period: K 线周期，如 ``"1d"`` / ``"1m"`` / ``"5m"``
            start_time: 开始时间，格式 ``"20230101"``
            end_time: 结束时间，格式同上
        """
        return self._post("/api/download/batch", {
            "stocks": stocks,
            "period": period,
            "start_time": start_time,
            "end_time": end_time,
        })

    def download_sector_data(self) -> dict:
        """Trigger sector data download."""
        return self._post("/api/download/sector_data", {})

    def download_index_weight(self) -> dict:
        """Trigger index weight data download."""
        return self._post("/api/download/index_weight", {})

    def download_etf_info(self) -> dict:
        """Trigger ETF info download."""
        return self._post("/api/download/etf_info", {})

    def download_cb_data(self) -> dict:
        """Trigger convertible bond data download."""
        return self._post("/api/download/cb_data", {})

    def download_history_contracts(self) -> dict:
        """Trigger expired contracts download."""
        return self._post("/api/download/history_contracts", {})

    def download_ipo_data(self) -> dict:
        """Trigger IPO data download."""
        return self._post("/api/download/ipo_data", {})

    def download_option_data(self) -> dict:
        """Trigger option data download."""
        return self._post("/api/download/option_data", {})


    def download_financial_data2(
        self, stocks: list[str], tables: list[str] | None = None
    ) -> dict:
        """同步下载财务数据（阻塞直至完成）。

        Args:
            stocks: 股票代码列表
            tables: 财务表名列表，如 ``["Balance", "Income"]``，为空则下载全部
        """
        return self._post("/api/download/financial2", {
            "stocks": stocks,
            "tables": tables or [],
        })

    def download_holiday_data(self) -> dict:
        """Download holiday calendar data."""
        return self._post("/api/download/holiday", {})

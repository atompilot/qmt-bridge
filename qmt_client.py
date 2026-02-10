"""QMT Bridge Python client — use on Mac/Linux to access the remote QMT Bridge server."""

import asyncio
import json
import urllib.request
from typing import Callable, Optional

import pandas as pd


class QMTClient:
    """Lightweight HTTP/WebSocket client for QMT Bridge server."""

    def __init__(self, host: str, port: int = 8000):
        self.base_url = f"http://{host}:{port}"
        self.ws_url = f"ws://{host}:{port}"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get(self, path: str, params: Optional[dict] = None) -> dict:
        """Send a GET request and return parsed JSON."""
        if params:
            query = "&".join(
                f"{k}={urllib.request.quote(str(v))}" for k, v in params.items() if v is not None
            )
            url = f"{self.base_url}{path}?{query}"
        else:
            url = f"{self.base_url}{path}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())

    def _post(self, path: str, body: dict) -> dict:
        """Send a POST request with JSON body and return parsed JSON."""
        url = f"{self.base_url}{path}"
        data = json.dumps(body).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())

    def _records_to_dataframes(self, data: dict) -> dict[str, pd.DataFrame]:
        """Convert {stock: [records]} to {stock: DataFrame}."""
        result: dict[str, pd.DataFrame] = {}
        for stock, records in data.items():
            if not records:
                result[stock] = pd.DataFrame()
                continue
            result[stock] = pd.DataFrame(records)
        return result

    # ------------------------------------------------------------------
    # Legacy API — REST (backward compatible)
    # ------------------------------------------------------------------

    def get_history(
        self,
        stock: str,
        period: str = "1d",
        count: int = 100,
        fields: str = "open,high,low,close,volume",
    ) -> pd.DataFrame:
        """Fetch historical K-line data for a single stock."""
        resp = self._get("/api/history", {
            "stock": stock,
            "period": period,
            "count": count,
            "fields": fields,
        })
        records = resp.get("data", [])
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
    ) -> dict[str, pd.DataFrame]:
        """Fetch historical data for multiple stocks."""
        resp = self._get("/api/batch_history", {
            "stocks": ",".join(stocks),
            "period": period,
            "count": count,
            "fields": fields,
        })
        data = resp.get("data", {})
        result: dict[str, pd.DataFrame] = {}
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

    def get_sector_stocks(self, sector: str) -> list[str]:
        """Fetch all stock codes in a given sector."""
        resp = self._get("/api/sector_stocks", {"sector": sector})
        return resp.get("stocks", [])

    def get_instrument_detail(self, stock: str) -> dict:
        """Fetch instrument details for a stock."""
        resp = self._get("/api/instrument_detail", {"stock": stock})
        return resp.get("detail", {})

    def download(self, stock: str, period: str = "1d", start: str = "", end: str = "") -> dict:
        """Trigger history data download on the server side."""
        return self._post("/api/download", {
            "stock": stock,
            "period": period,
            "start": start,
            "end": end,
        })

    # ------------------------------------------------------------------
    # Market data (P0/P1)
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
    ) -> dict[str, pd.DataFrame]:
        """Fetch enhanced K-line data with dividend adjustment support."""
        resp = self._get("/api/market/history_ex", {
            "stocks": ",".join(stocks),
            "period": period,
            "start_time": start_time,
            "end_time": end_time,
            "count": count,
            "dividend_type": dividend_type,
            "fill_data": fill_data,
        })
        return self._records_to_dataframes(resp.get("data", {}))

    def get_local_data(
        self,
        stocks: list[str],
        period: str = "1d",
        start_time: str = "",
        end_time: str = "",
        count: int = -1,
        dividend_type: str = "none",
        fill_data: bool = True,
    ) -> dict[str, pd.DataFrame]:
        """Read data from local cache only (offline capable)."""
        resp = self._get("/api/market/local_data", {
            "stocks": ",".join(stocks),
            "period": period,
            "start_time": start_time,
            "end_time": end_time,
            "count": count,
            "dividend_type": dividend_type,
            "fill_data": fill_data,
        })
        return self._records_to_dataframes(resp.get("data", {}))

    def get_market_snapshot(self, stocks: list[str]) -> dict:
        """Fetch real-time tick snapshot for given stocks/indices."""
        resp = self._get("/api/market/snapshot", {"stocks": ",".join(stocks)})
        return resp.get("data", {})

    def get_major_indices(self) -> dict:
        """Fetch real-time snapshot of major market indices."""
        resp = self._get("/api/market/indices")
        return resp

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

    # ------------------------------------------------------------------
    # Sector (P0/P1)
    # ------------------------------------------------------------------

    def get_sector_list(self) -> list[str]:
        """Fetch all available sector names."""
        resp = self._get("/api/sector/list")
        return resp.get("sectors", [])

    def get_sector_info(self, sector: str = "") -> dict:
        """Fetch sector metadata."""
        resp = self._get("/api/sector/info", {"sector": sector})
        return resp.get("data", {})

    def get_sector_stocks_v2(
        self, sector: str, real_timetag: int = -1
    ) -> list[str]:
        """Fetch stock codes in a sector (new endpoint, supports historical composition).

        Examples::

            client.get_sector_stocks_v2("沪深A股")
            client.get_sector_stocks_v2("沪深300")
            client.get_sector_stocks_v2("沪深ETF")
        """
        resp = self._get("/api/sector/stocks", {
            "sector": sector,
            "real_timetag": real_timetag,
        })
        return resp.get("stocks", [])

    # ------------------------------------------------------------------
    # Calendar (P0/P1/P2)
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Financial (P0)
    # ------------------------------------------------------------------

    def get_financial_data(
        self,
        stocks: list[str],
        tables: list[str] | None = None,
        start_time: str = "",
        end_time: str = "",
        report_type: str = "report_time",
    ) -> dict:
        """Fetch financial statement data (Balance/Income/CashFlow etc.)."""
        resp = self._get("/api/financial/data", {
            "stocks": ",".join(stocks),
            "tables": ",".join(tables) if tables else "",
            "start_time": start_time,
            "end_time": end_time,
            "report_type": report_type,
        })
        return resp.get("data", {})

    def download_financial(
        self,
        stocks: list[str],
        tables: list[str] | None = None,
        start_time: str = "",
        end_time: str = "",
    ) -> dict:
        """Trigger financial data download on the server."""
        return self._post("/api/download/financial", {
            "stocks": stocks,
            "tables": tables or [],
            "start_time": start_time,
            "end_time": end_time,
        })

    # ------------------------------------------------------------------
    # Instrument (P0/P1/P2)
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Tick / L2 (P1/P2)
    # ------------------------------------------------------------------

    def get_l2_quote(
        self, stock: str, start_time: str = "", end_time: str = "", count: int = -1
    ) -> dict:
        """Fetch L2 quote snapshot."""
        resp = self._get("/api/tick/l2_quote", {
            "stock": stock,
            "start_time": start_time,
            "end_time": end_time,
            "count": count,
        })
        return resp.get("data", {})

    def get_l2_order(
        self, stock: str, start_time: str = "", end_time: str = "", count: int = -1
    ) -> dict:
        """Fetch L2 order-by-order data."""
        resp = self._get("/api/tick/l2_order", {
            "stock": stock,
            "start_time": start_time,
            "end_time": end_time,
            "count": count,
        })
        return resp.get("data", {})

    def get_l2_transaction(
        self, stock: str, start_time: str = "", end_time: str = "", count: int = -1
    ) -> dict:
        """Fetch L2 transaction-by-transaction data."""
        resp = self._get("/api/tick/l2_transaction", {
            "stock": stock,
            "start_time": start_time,
            "end_time": end_time,
            "count": count,
        })
        return resp.get("data", {})

    # ------------------------------------------------------------------
    # Option (P1/P2)
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # ETF & Convertible Bond (P1/P2)
    # ------------------------------------------------------------------

    def get_etf_list(self) -> list[str]:
        """Fetch lightweight ETF code list."""
        resp = self._get("/api/etf/list")
        return resp.get("stocks", [])

    def get_etf_info(self) -> dict:
        """Fetch ETF subscription/redemption list."""
        resp = self._get("/api/etf/info")
        return resp.get("data", {})

    def get_cb_info(self, stock: str) -> dict:
        """Fetch convertible bond information."""
        resp = self._get("/api/cb/info", {"stock": stock})
        return resp.get("data", {})

    # ------------------------------------------------------------------
    # Futures (P1/P2)
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Meta (P0)
    # ------------------------------------------------------------------

    def get_markets(self) -> dict:
        """Fetch available markets."""
        resp = self._get("/api/meta/markets")
        return resp.get("markets", {})

    def get_periods(self) -> list:
        """Fetch available K-line periods."""
        resp = self._get("/api/meta/periods")
        return resp.get("periods", [])

    def get_stock_list_by_category(self, category: str) -> list[str]:
        """Fetch stock codes by category (e.g. 沪深A股, 沪深ETF, 沪深指数)."""
        resp = self._get("/api/meta/stock_list", {"category": category})
        return resp.get("stocks", [])

    def get_last_trade_date(self, market: str) -> str:
        """Fetch the last trade date for a market (e.g. SH, SZ)."""
        resp = self._get("/api/meta/last_trade_date", {"market": market})
        return resp.get("last_trade_date", "")

    # ------------------------------------------------------------------
    # Download (P0/P1/P2)
    # ------------------------------------------------------------------

    def download_batch(
        self,
        stocks: list[str],
        period: str = "1d",
        start_time: str = "",
        end_time: str = "",
    ) -> dict:
        """Trigger batch history data download."""
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

    # ------------------------------------------------------------------
    # WebSocket — realtime (legacy)
    # ------------------------------------------------------------------

    async def subscribe_realtime(
        self,
        stocks: list[str],
        callback: Callable[[dict], None],
        period: str = "tick",
    ):
        """Subscribe to realtime quote updates via WebSocket.

        This is a coroutine that runs indefinitely until cancelled or the
        connection drops.  Requires the ``websockets`` package::

            pip install websockets

        Usage::

            import asyncio
            from qmt_client import QMTClient

            client = QMTClient("192.168.1.100")

            def on_tick(data):
                print(data)

            asyncio.run(client.subscribe_realtime(
                stocks=["000001.SZ", "600519.SH"],
                callback=on_tick,
            ))
        """
        try:
            import websockets
        except ImportError:
            raise ImportError(
                "websockets package is required for realtime subscriptions. "
                "Install it with: pip install websockets"
            )

        url = f"{self.ws_url}/ws/realtime"
        async with websockets.connect(url) as ws:
            await ws.send(json.dumps({"stocks": stocks, "period": period}))
            async for message in ws:
                data = json.loads(message)
                callback(data)

    # ------------------------------------------------------------------
    # WebSocket — whole market quote
    # ------------------------------------------------------------------

    async def subscribe_whole_quote(
        self,
        codes: list[str],
        callback: Callable[[dict], None],
    ):
        """Subscribe to whole-market quote updates via WebSocket.

        Requires the ``websockets`` package.
        """
        try:
            import websockets
        except ImportError:
            raise ImportError(
                "websockets package is required. Install with: pip install websockets"
            )

        url = f"{self.ws_url}/ws/whole_quote"
        async with websockets.connect(url) as ws:
            await ws.send(json.dumps({"codes": codes}))
            async for message in ws:
                data = json.loads(message)
                callback(data)

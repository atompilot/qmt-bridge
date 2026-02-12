"""MarketMixin — 行情数据客户端方法。

封装了与行情相关的所有客户端接口，包括：
- 历史 K 线查询（普通版和增强版）
- 实时行情快照
- 除权因子查询
- 本地缓存数据读取
- 逐笔/委托簿数据

底层对应 xtquant 的 ``xtdata.get_market_data()``、``xtdata.get_full_tick()``、
``xtdata.get_local_data()`` 等函数。
"""

from typing import Optional


class MarketMixin:
    """行情数据客户端方法集合，对应 /api/market/* 及旧版行情端点。"""

    # ------------------------------------------------------------------
    # 旧版 API（保留向后兼容）
    # ------------------------------------------------------------------

    def get_history(
        self,
        stock: str,
        period: str = "1d",
        count: int = 100,
        fields: str = "open,high,low,close,volume",
    ):
        """获取单只股票的历史 K 线数据。

        这是旧版接口，推荐使用 ``get_history_ex()`` 获取更丰富的功能。

        底层调用 xtquant 的 ``xtdata.get_market_data()``，按指定周期和数量
        返回 OHLCV 等字段的历史行情。

        Args:
            stock: 股票代码，如 ``"000001.SZ"``（平安银行）
            period: K 线周期 — ``"1m"``/``"5m"``/``"15m"``/``"30m"``/``"1h"``/``"1d"``/``"1w"``/``"1mon"``
            count: 返回条数，从最新一根 K 线往前取
            fields: 返回字段，逗号分隔，可选: open/high/low/close/volume/amount/settelementPrice 等

        Returns:
            安装了 pandas 时返回 DataFrame（以 date 为索引），否则返回 list[dict]
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

        一次请求获取多只股票的 K 线，避免逐个请求的网络开销。
        底层对应服务端的 ``/api/batch_history`` 端点。

        Args:
            stocks: 股票代码列表，如 ``["000001.SZ", "600519.SH"]``
            period: K 线周期，如 ``"1d"``/``"1m"``/``"5m"``/``"1w"``
            count: 每只股票返回的 K 线条数
            fields: 返回字段，逗号分隔

        Returns:
            安装了 pandas 时返回 ``dict[str, DataFrame]``，否则返回 ``dict[str, list[dict]]``
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
        """获取指定股票的最新 Tick 快照数据。

        底层调用 ``xtdata.get_full_tick()``，返回包含最新价、买卖盘口、
        成交量等完整 Tick 级别信息。

        Args:
            stocks: 股票代码列表

        Returns:
            以股票代码为键的快照数据字典
        """
        resp = self._get("/api/full_tick", {"stocks": ",".join(stocks)})
        return resp.get("data", {})

    def get_instrument_detail(self, stock: str) -> dict:
        """获取合约详情（旧版接口）。

        返回股票/期货/期权的合约基本信息，如名称、上市日期、涨跌停价等。
        底层调用 ``xtdata.get_instrument_detail()``。

        Args:
            stock: 合约代码，如 ``"000001.SZ"``

        Returns:
            合约详情字典
        """
        resp = self._get("/api/instrument_detail", {"stock": stock})
        return resp.get("detail", {})

    def download(self, stock: str, period: str = "1d", start: str = "", end: str = "") -> dict:
        """触发服务端下载历史数据（旧版接口）。

        向服务端发起数据下载请求，数据会缓存到服务端本地。
        下载完成后可通过 ``get_local_data()`` 读取。

        Args:
            stock: 股票代码
            period: K 线周期
            start: 开始时间，格式 ``"20230101"``
            end: 结束时间

        Returns:
            下载结果信息
        """
        return self._post("/api/download", {
            "stock": stock,
            "period": period,
            "start": start,
            "end": end,
        })

    # ------------------------------------------------------------------
    # 新版行情 API
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

        底层调用 ``xtdata.get_market_data_ex()``，相比旧版 ``get_history()``：
        - 支持前/后复权（含等比复权）
        - 支持停牌期间数据填充
        - 支持时间范围筛选

        Args:
            stocks: 股票代码列表，如 ``["000001.SZ", "600519.SH"]``
            period: K 线周期 — ``"1m"``/``"5m"``/``"15m"``/``"30m"``/``"1h"``/``"1d"``/``"1w"``/``"1mon"``
            start_time: 开始时间，格式 ``"20230101"`` 或 ``"20230101093000"``
            end_time: 结束时间，格式同上
            count: 返回条数，-1 表示返回时间范围内全部数据
            dividend_type: 除权类型:
                - ``"none"``: 不复权
                - ``"front"``: 前复权
                - ``"back"``: 后复权
                - ``"front_ratio"``: 等比前复权
                - ``"back_ratio"``: 等比后复权
            fill_data: 是否填充停牌等缺失数据（用前一交易日收盘价填充）

        Returns:
            ``dict[str, DataFrame]``（安装了 pandas 时），否则为 ``dict[str, list[dict]]``
        """
        resp = self._get("/api/market/market_data_ex", {
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

        底层调用 ``xtdata.get_local_data()``，与 ``get_history_ex()`` 参数相同，
        区别在于本方法不会触发网络请求向行情服务器拉取数据，仅读取已通过
        ``download_batch()`` 等方法下载到服务端本地的数据。

        适用场景：
        - 离线分析已下载的数据
        - 避免频繁请求行情服务器
        - 在网络不稳定时使用本地数据

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

        底层调用 ``xtdata.get_full_tick()``，返回最新的盘口快照数据，
        包括最新价、涨跌幅、买卖五档、成交量等。

        Args:
            stocks: 股票代码列表，如 ``["000001.SZ", "000001.SH"]``

        Returns:
            以股票代码为键的快照数据字典
        """
        resp = self._get("/api/market/full_tick", {"stocks": ",".join(stocks)})
        return resp.get("data", {})

    def get_major_indices(self) -> dict:
        """获取主要市场指数的实时快照。

        返回上证指数、深证成指、创业板指、沪深300等预设的主要指数的实时行情。

        Returns:
            以指数代码为键的快照数据字典
        """
        return self._get("/api/market/indices")

    def get_divid_factors(
        self, stock: str, start_time: str = "", end_time: str = ""
    ) -> dict:
        """获取除权除息因子数据。

        底层调用 ``xtdata.get_divid_factors()``，返回股票在指定时间范围内的
        分红送股、配股等除权因子信息，可用于手动计算复权价格。

        Args:
            stock: 股票代码，如 ``"000001.SZ"``
            start_time: 开始时间，格式 ``"20230101"``
            end_time: 结束时间

        Returns:
            除权因子数据字典
        """
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
        """通过 xtdata.get_market_data() 原始接口获取行情数据。

        返回格式为 ``{field: {stock: [values]}}``，即按字段组织的嵌套字典。
        此接口保留了 xtquant 原始返回结构，适合需要按字段批量处理数据的场景。

        Args:
            stocks: 股票代码列表
            fields: 返回字段，逗号分隔（open/high/low/close/volume/amount 等）
            period: K 线周期
            start_time: 开始时间
            end_time: 结束时间
            count: 返回条数，-1 表示全部
            dividend_type: 除权类型
            fill_data: 是否填充缺失数据

        Returns:
            原始格式的行情数据字典
        """
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
        """通过 xtdata.get_market_data3() 新版接口获取行情数据。

        与 ``get_market_data()`` 的区别在于返回格式为 ``{stock: DataFrame}``，
        每只股票的数据组织为独立的 DataFrame，更适合按个股分析的场景。

        Args:
            stocks: 股票代码列表
            fields: 返回字段（为空则返回全部字段）
            period: K 线周期
            start_time: 开始时间
            end_time: 结束时间
            count: 返回条数，-1 表示全部
            dividend_type: 除权类型
            fill_data: 是否填充缺失数据

        Returns:
            ``dict[str, DataFrame]``（安装了 pandas 时），否则为 ``dict[str, list[dict]]``
        """
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
        """获取单只股票的完整 K 线数据。

        底层调用 ``xtdata.get_full_kline()``，一次性返回指定时间范围内
        所有 K 线数据，适合需要完整历史数据的场景。

        Args:
            stock: 股票代码
            period: K 线周期
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            K 线数据字典
        """
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
        """获取全速委托簿数据。

        底层调用 ``xtdata.get_fullspeed_orderbook()``，返回指定时间范围内
        的高频委托簿快照数据（买卖各档价量），适合高频策略和市场微结构分析。

        Args:
            stock: 股票代码
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            委托簿数据字典
        """
        resp = self._get("/api/market/fullspeed_orderbook", {
            "stock": stock,
            "start_time": start_time,
            "end_time": end_time,
        })
        return resp.get("data", {})

    def get_transactioncount(
        self, stock: str, start_time: str = "", end_time: str = ""
    ) -> dict:
        """获取成交笔数统计数据。

        底层调用 ``xtdata.get_transactioncount()``，返回指定时间范围内
        每个时间切片的成交笔数统计，可用于分析市场活跃度和资金流向。

        Args:
            stock: 股票代码
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            成交笔数数据字典
        """
        resp = self._get("/api/market/transactioncount", {
            "stock": stock,
            "start_time": start_time,
            "end_time": end_time,
        })
        return resp.get("data", {})

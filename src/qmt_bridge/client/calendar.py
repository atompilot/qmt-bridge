"""CalendarMixin — 交易日历客户端方法。

封装了交易日历相关的查询接口，包括：
- 交易日期查询（历史和未来）
- 节假日列表
- 交易时段信息
- 交易日判断和前后交易日查询

底层对应 xtquant 的 ``xtdata.get_trading_dates()``、
``xtdata.get_holidays()``、``xtdata.get_trading_calendar()`` 等函数。
"""


class CalendarMixin:
    """交易日历客户端方法集合，对应 /api/calendar/* 端点。"""

    def get_trading_dates(
        self, market: str, start_time: str = "", end_time: str = "", count: int = -1
    ) -> list:
        """获取指定市场的交易日期列表。

        底层调用 ``xtdata.get_trading_dates()``，返回指定市场在时间范围内
        的所有交易日期。

        Args:
            market: 市场代码，如 ``"SH"``（上海）、``"SZ"``（深圳）
            start_time: 开始时间，格式 ``"20230101"``
            end_time: 结束时间
            count: 返回条数，-1 表示全部

        Returns:
            交易日期列表（时间戳格式）
        """
        resp = self._get("/api/calendar/trading_dates", {
            "market": market,
            "start_time": start_time,
            "end_time": end_time,
            "count": count,
        })
        return resp.get("dates", [])

    def get_holidays(self) -> list:
        """获取节假日列表。

        底层调用 ``xtdata.get_holidays()``，返回交易所公布的全部节假日日期。

        Returns:
            节假日日期列表
        """
        resp = self._get("/api/calendar/holidays")
        return resp.get("holidays", [])

    def get_trading_calendar(
        self, market: str, start_time: str = "", end_time: str = ""
    ) -> list:
        """获取完整交易日历（含未来日期预测）。

        底层调用 ``xtdata.get_trading_calendar()``，返回含未来交易日的
        完整日历数据。

        Args:
            market: 市场代码
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            交易日历列表
        """
        resp = self._get("/api/calendar/trading_calendar", {
            "market": market,
            "start_time": start_time,
            "end_time": end_time,
        })
        return resp.get("calendar", [])

    def get_trading_period(self, stock: str) -> list:
        """获取股票的交易时段信息。

        底层调用 ``xtdata.get_trading_period()``，返回指定股票（或其所在市场）
        的交易时段划分，如上午开盘/收盘时间、下午开盘/收盘时间等。
        不同品种（股票/期货/期权）的交易时段可能不同。

        Args:
            stock: 股票代码，如 ``"000001.SZ"``

        Returns:
            交易时段列表
        """
        resp = self._get("/api/calendar/trading_period", {"stock": stock})
        return resp.get("periods", [])

    def is_trading_date(self, market: str, date: str) -> bool:
        """判断指定日期是否为交易日。

        Args:
            market: 市场代码，如 ``"SH"``
            date: 日期字符串，格式 ``"20230101"``

        Returns:
            True 表示是交易日，False 表示非交易日（周末或节假日）
        """
        resp = self._get("/api/calendar/is_trading_date", {
            "market": market,
            "date": date,
        })
        return resp.get("is_trading", False)

    def get_prev_trading_date(self, market: str, date: str = "") -> str | None:
        """获取上一个交易日。

        Args:
            market: 市场代码
            date: 基准日期，为空时使用当天

        Returns:
            上一个交易日的日期字符串，无结果时返回 None
        """
        resp = self._get("/api/calendar/prev_trading_date", {
            "market": market,
            "date": date,
        })
        return resp.get("prev_trading_date")

    def get_next_trading_date(self, market: str, date: str = "") -> str | None:
        """获取下一个交易日。

        Args:
            market: 市场代码
            date: 基准日期，为空时使用当天

        Returns:
            下一个交易日的日期字符串，无结果时返回 None
        """
        resp = self._get("/api/calendar/next_trading_date", {
            "market": market,
            "date": date,
        })
        return resp.get("next_trading_date")

    def get_trading_dates_count(
        self, market: str, start_time: str = "", end_time: str = ""
    ) -> int:
        """统计时间范围内的交易日数量。

        Args:
            market: 市场代码
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            交易日数量
        """
        resp = self._get("/api/calendar/trading_dates_count", {
            "market": market,
            "start_time": start_time,
            "end_time": end_time,
        })
        return resp.get("count", 0)


"""交易日历路由模块 /api/calendar/*。

提供交易日查询、节假日查询、交易时段查询等日历相关端点。
底层调用 xtquant.xtdata 的日历接口，包括：
- xtdata.get_trading_dates()     — 获取交易日列表
- xtdata.get_holidays()          — 获取节假日列表
- xtdata.get_trading_calendar()  — 获取交易日历
- xtdata.get_trading_period()    — 获取合约交易时段
"""

from fastapi import APIRouter, Query
from xtquant import xtdata

from ..helpers import _numpy_to_python

router = APIRouter(prefix="/api/calendar", tags=["calendar"])


@router.get("/trading_dates")
def get_trading_dates(
    market: str = Query(..., description="市场代码，如 SH/SZ/IF/DF/SF/ZF"),
    start_time: str = Query("", description="开始时间 YYYYMMDD"),
    end_time: str = Query("", description="结束时间 YYYYMMDD"),
    count: int = Query(-1, description="返回条数"),
):
    """获取指定市场的交易日列表。

    Args:
        market: 市场代码（SH=上海、SZ=深圳、IF=中金所、DF=大商所、SF=上期所、ZF=郑商所）。
        start_time: 起始日期，格式 YYYYMMDD。
        end_time: 结束日期，格式 YYYYMMDD。
        count: 返回条数，-1 表示不限。

    Returns:
        market: 市场代码。
        dates: 交易日列表（时间戳数组）。

    底层调用: xtdata.get_trading_dates(market, start_time=..., end_time=..., count=...)
    """
    raw = xtdata.get_trading_dates(
        market, start_time=start_time, end_time=end_time, count=count
    )
    return {"market": market, "dates": _numpy_to_python(raw)}


@router.get("/holidays")
def get_holidays():
    """获取全部节假日列表。

    Returns:
        holidays: 节假日信息列表。

    底层调用: xtdata.get_holidays()
    """
    raw = xtdata.get_holidays()
    return {"holidays": _numpy_to_python(raw)}


@router.get("/trading_calendar")
def get_trading_calendar(
    market: str = Query(..., description="市场代码"),
    start_time: str = Query("", description="开始时间"),
    end_time: str = Query("", description="结束时间"),
):
    """获取指定市场的交易日历。

    交易日历包含每个自然日是否为交易日的标记信息。

    Args:
        market: 市场代码。
        start_time: 开始时间。
        end_time: 结束时间。

    Returns:
        market: 市场代码。
        calendar: 交易日历数据。

    底层调用: xtdata.get_trading_calendar(market, start_time=..., end_time=...)
    """
    raw = xtdata.get_trading_calendar(market, start_time=start_time, end_time=end_time)
    return {"market": market, "calendar": _numpy_to_python(raw)}


@router.get("/trading_period")
def get_trading_period(
    stock: str = Query(..., description="合约代码，如 000001.SZ"),
):
    """获取指定合约的交易时段信息。

    返回该合约每个交易时段的起止时间（如上午 9:30-11:30，下午 13:00-15:00）。

    Args:
        stock: 合约代码。

    Returns:
        stock: 合约代码。
        periods: 交易时段列表。

    底层调用: xtdata.get_trading_period(stock)
    """
    raw = xtdata.get_trading_period(stock)
    return {"stock": stock, "periods": _numpy_to_python(raw)}


# ---------------------------------------------------------------------------
# 扩展交易日历端点
# ---------------------------------------------------------------------------


@router.get("/is_trading_date")
def is_trading_date(
    market: str = Query(..., description="市场代码"),
    date: str = Query(..., description="日期 YYYYMMDD"),
):
    """判断指定日期是否为交易日。

    通过查询该日期范围内的交易日列表，判断该日期是否在其中。

    Args:
        market: 市场代码。
        date: 日期，格式 YYYYMMDD。

    Returns:
        is_trading: 布尔值，True 表示是交易日。

    底层调用: xtdata.get_trading_dates(market, start_time=date, end_time=date)
    """
    raw = xtdata.get_trading_dates(market, start_time=date, end_time=date)
    dates = _numpy_to_python(raw)
    # 如果指定日期范围内存在交易日，则说明该日期是交易日
    return {"market": market, "date": date, "is_trading": len(dates) > 0}


@router.get("/prev_trading_date")
def get_prev_trading_date(
    market: str = Query(..., description="市场代码"),
    date: str = Query("", description="参考日期 YYYYMMDD，默认今天"),
):
    """获取指定日期的前一个交易日。

    查询截至指定日期的最后两个交易日，取倒数第二个作为前一交易日。

    Args:
        market: 市场代码。
        date: 参考日期，默认为今天。

    Returns:
        prev_trading_date: 前一交易日时间戳。

    底层调用: xtdata.get_trading_dates(market, end_time=date, count=2)
    """
    raw = xtdata.get_trading_dates(market, end_time=date, count=2)
    dates = _numpy_to_python(raw)
    if len(dates) >= 2:
        # 倒数第二个即为前一交易日
        return {"market": market, "prev_trading_date": dates[-2]}
    return {"market": market, "prev_trading_date": dates[0] if dates else None}


@router.get("/next_trading_date")
def get_next_trading_date(
    market: str = Query(..., description="市场代码"),
    date: str = Query("", description="参考日期 YYYYMMDD，默认今天"),
):
    """获取指定日期的下一个交易日。

    查询从指定日期开始的前两个交易日，取第二个作为下一交易日。

    Args:
        market: 市场代码。
        date: 参考日期，默认为今天。

    Returns:
        next_trading_date: 下一交易日时间戳。

    底层调用: xtdata.get_trading_dates(market, start_time=date, count=2)
    """
    raw = xtdata.get_trading_dates(market, start_time=date, count=2)
    dates = _numpy_to_python(raw)
    if len(dates) >= 2:
        # 第二个即为下一交易日
        return {"market": market, "next_trading_date": dates[1]}
    return {"market": market, "next_trading_date": dates[0] if dates else None}


@router.get("/trading_dates_count")
def get_trading_dates_count(
    market: str = Query(..., description="市场代码"),
    start_time: str = Query("", description="开始时间"),
    end_time: str = Query("", description="结束时间"),
):
    """统计指定时间范围内的交易日数量。

    Args:
        market: 市场代码。
        start_time: 开始时间。
        end_time: 结束时间。

    Returns:
        count: 交易日数量。

    底层调用: xtdata.get_trading_dates(market, start_time=..., end_time=...)
    """
    raw = xtdata.get_trading_dates(market, start_time=start_time, end_time=end_time)
    dates = _numpy_to_python(raw)
    return {"market": market, "count": len(dates)}



"""Router — Market data endpoints /api/market/*."""

from fastapi import APIRouter, Query
from xtquant import xtdata

from ..helpers import _dataframe_dict_to_records, _numpy_to_python

router = APIRouter(prefix="/api/market", tags=["market"])

# 主要指数列表（用于 /indices 端点）
MAJOR_INDICES = [
    "000001.SH",  # 上证指数
    "399001.SZ",  # 深证成指
    "399006.SZ",  # 创业板指
    "000300.SH",  # 沪深300
    "000016.SH",  # 上证50
    "000905.SH",  # 中证500
    "000852.SH",  # 中证1000
]


@router.get("/snapshot")
def get_market_snapshot(
    stocks: str = Query(..., description="股票/指数代码列表，逗号分隔，如 000001.SH,000001.SZ"),
):
    stock_list = [s.strip() for s in stocks.split(",")]
    raw = xtdata.get_full_tick(code_list=stock_list)
    return {"data": _numpy_to_python(raw)}


@router.get("/indices")
def get_major_indices():
    raw = xtdata.get_full_tick(code_list=MAJOR_INDICES)
    return {"indices": MAJOR_INDICES, "data": _numpy_to_python(raw)}


@router.get("/history_ex")
def get_history_ex(
    stocks: str = Query(..., description="股票代码列表，逗号分隔，如 000001.SZ,600519.SH"),
    period: str = Query("1d", description="K线周期: tick/1m/5m/15m/30m/60m/1d"),
    start_time: str = Query("", description="开始时间 YYYYMMDD 或 YYYYMMDDHHmmss"),
    end_time: str = Query("", description="结束时间"),
    count: int = Query(-1, description="返回条数，-1 表示不限"),
    dividend_type: str = Query("none", description="除权类型: none/front/back/front_ratio/back_ratio"),
    fill_data: bool = Query(True, description="是否填充空数据"),
):
    stock_list = [s.strip() for s in stocks.split(",")]
    raw = xtdata.get_market_data_ex(
        field_list=[],
        stock_list=stock_list,
        period=period,
        start_time=start_time,
        end_time=end_time,
        count=count,
        dividend_type=dividend_type,
        fill_data=fill_data,
    )
    return {"data": _dataframe_dict_to_records(raw)}


@router.get("/local_data")
def get_local_data(
    stocks: str = Query(..., description="股票代码列表，逗号分隔"),
    period: str = Query("1d", description="K线周期"),
    start_time: str = Query("", description="开始时间"),
    end_time: str = Query("", description="结束时间"),
    count: int = Query(-1, description="返回条数"),
    dividend_type: str = Query("none", description="除权类型"),
    fill_data: bool = Query(True, description="是否填充空数据"),
):
    stock_list = [s.strip() for s in stocks.split(",")]
    raw = xtdata.get_local_data(
        field_list=[],
        stock_list=stock_list,
        period=period,
        start_time=start_time,
        end_time=end_time,
        count=count,
        dividend_type=dividend_type,
        fill_data=fill_data,
    )
    return {"data": _dataframe_dict_to_records(raw)}


@router.get("/divid_factors")
def get_divid_factors(
    stock: str = Query(..., description="股票代码，如 000001.SZ"),
    start_time: str = Query("", description="开始时间"),
    end_time: str = Query("", description="结束时间"),
):
    raw = xtdata.get_divid_factors(stock, start_time=start_time, end_time=end_time)
    return {"stock": stock, "data": _numpy_to_python(raw)}


# ---------------------------------------------------------------------------
# New endpoints (Step 5)
# ---------------------------------------------------------------------------


@router.get("/market_data")
def get_market_data(
    stocks: str = Query(..., description="股票代码列表，逗号分隔"),
    fields: str = Query("open,high,low,close,volume", description="字段列表，逗号分隔"),
    period: str = Query("1d", description="K线周期"),
    start_time: str = Query("", description="开始时间"),
    end_time: str = Query("", description="结束时间"),
    count: int = Query(-1, description="返回条数"),
    dividend_type: str = Query("none", description="除权类型"),
    fill_data: bool = Query(True, description="是否填充空数据"),
):
    """Get market data via get_market_data (original API)."""
    from ..helpers import _market_data_to_records

    stock_list = [s.strip() for s in stocks.split(",")]
    field_list = [f.strip() for f in fields.split(",")]
    raw = xtdata.get_market_data(
        field_list=field_list,
        stock_list=stock_list,
        period=period,
        start_time=start_time,
        end_time=end_time,
        count=count,
        dividend_type=dividend_type,
        fill_data=fill_data,
    )
    records = _market_data_to_records(raw, stock_list, field_list)
    return {"data": records}


@router.get("/market_data3")
def get_market_data3(
    stocks: str = Query(..., description="股票代码列表，逗号分隔"),
    fields: str = Query("", description="字段列表，逗号分隔，为空取全部"),
    period: str = Query("1d", description="K线周期"),
    start_time: str = Query("", description="开始时间"),
    end_time: str = Query("", description="结束时间"),
    count: int = Query(-1, description="返回条数"),
    dividend_type: str = Query("none", description="除权类型"),
    fill_data: bool = Query(True, description="是否填充空数据"),
):
    """Get market data via get_market_data3 (returns dict of DataFrames)."""
    stock_list = [s.strip() for s in stocks.split(",")]
    field_list = [f.strip() for f in fields.split(",") if f.strip()] if fields else []
    raw = xtdata.get_market_data3(
        field_list=field_list,
        stock_list=stock_list,
        period=period,
        start_time=start_time,
        end_time=end_time,
        count=count,
        dividend_type=dividend_type,
        fill_data=fill_data,
    )
    return {"data": _dataframe_dict_to_records(raw)}


@router.get("/full_kline")
def get_full_kline(
    stock: str = Query(..., description="股票代码"),
    period: str = Query("1d", description="K线周期"),
    start_time: str = Query("", description="开始时间"),
    end_time: str = Query("", description="结束时间"),
):
    """Get full K-line data for a single stock."""
    raw = xtdata.get_full_kline(stock, period=period, start_time=start_time, end_time=end_time)
    return {"stock": stock, "data": _numpy_to_python(raw)}


@router.get("/fullspeed_orderbook")
def get_fullspeed_orderbook(
    stock: str = Query(..., description="股票代码"),
    start_time: str = Query("", description="开始时间"),
    end_time: str = Query("", description="结束时间"),
):
    """Get full-speed order book data."""
    raw = xtdata.get_fullspeed_orderbook(stock, start_time=start_time, end_time=end_time)
    return {"stock": stock, "data": _numpy_to_python(raw)}


@router.get("/transactioncount")
def get_transactioncount(
    stock: str = Query(..., description="股票代码"),
    start_time: str = Query("", description="开始时间"),
    end_time: str = Query("", description="结束时间"),
):
    """Get transaction count data."""
    raw = xtdata.get_transactioncount(stock, start_time=start_time, end_time=end_time)
    return {"stock": stock, "data": _numpy_to_python(raw)}

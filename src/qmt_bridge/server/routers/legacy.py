"""旧版兼容路由模块（无前缀，直接挂载在 /api/ 下）。

提供向后兼容的旧版 API 端点，这些端点是早期 server.py 单文件版本中定义的接口。
新开发请使用对应模块化路由（如 /api/market/*、/api/sector/* 等）。
底层调用 xtquant.xtdata 的接口，包括：
- xtdata.get_market_data()            — 获取行情数据
- xtdata.get_full_tick()              — 获取全推行情快照
- xtdata.get_stock_list_in_sector()   — 获取板块成分股
- xtdata.get_instrument_detail()      — 获取合约详情
- xtdata.download_history_data()      — 下载历史数据（单只）
"""

from fastapi import APIRouter, Query
from xtquant import xtdata

from ..helpers import _market_data_to_records, _numpy_to_python
from ..models import DownloadRequest

# 旧版路由不带公共前缀，各端点自行定义完整路径
router = APIRouter(tags=["legacy"])


@router.get("/api/history")
def get_history(
    stock: str = Query(..., description="股票代码，如 000001.SZ"),
    period: str = Query("1d", description="K线周期: tick/1m/5m/15m/30m/60m/1d"),
    count: int = Query(100, description="返回条数"),
    fields: str = Query(
        "open,high,low,close,volume",
        description="字段列表，逗号分隔",
    ),
):
    """[旧版] 获取单只股票的历史 K 线数据。

    建议使用新版 /api/market/market_data 或 /api/market/market_data_ex 替代。

    Args:
        stock: 股票代码。
        period: K 线周期。
        count: 返回条数。
        fields: 逗号分隔的字段列表。

    Returns:
        stock: 股票代码。
        period: K 线周期。
        count: 请求条数。
        data: K 线记录列表。

    底层调用: xtdata.get_market_data(field_list=..., stock_list=[stock], ...)
    """
    field_list = [f.strip() for f in fields.split(",")]
    raw = xtdata.get_market_data(
        field_list=field_list,
        stock_list=[stock],
        period=period,
        count=count,
    )
    records = _market_data_to_records(raw, [stock], field_list)
    return {"stock": stock, "period": period, "count": count, "data": records.get(stock, [])}


@router.get("/api/batch_history")
def get_batch_history(
    stocks: str = Query(..., description="股票代码列表，逗号分隔"),
    period: str = Query("1d", description="K线周期"),
    count: int = Query(100, description="返回条数"),
    fields: str = Query(
        "open,high,low,close,volume",
        description="字段列表，逗号分隔",
    ),
):
    """[旧版] 批量获取多只股票的历史 K 线数据。

    建议使用新版 /api/market/market_data 替代。

    Args:
        stocks: 逗号分隔的股票代码列表。
        period: K 线周期。
        count: 返回条数。
        fields: 逗号分隔的字段列表。

    Returns:
        stocks: 股票代码列表。
        period: K 线周期。
        count: 请求条数。
        data: 按股票代码分组的 K 线记录。

    底层调用: xtdata.get_market_data(field_list=..., stock_list=..., ...)
    """
    stock_list = [s.strip() for s in stocks.split(",")]
    field_list = [f.strip() for f in fields.split(",")]
    raw = xtdata.get_market_data(
        field_list=field_list,
        stock_list=stock_list,
        period=period,
        count=count,
    )
    records = _market_data_to_records(raw, stock_list, field_list)
    return {"stocks": stock_list, "period": period, "count": count, "data": records}


@router.get("/api/full_tick")
def get_full_tick(
    stocks: str = Query(..., description="股票代码列表，逗号分隔"),
):
    """[旧版] 获取全推行情快照。

    建议使用新版 /api/market/full_tick 替代。

    Args:
        stocks: 逗号分隔的股票代码列表。

    Returns:
        data: 各股票的全推行情数据。

    底层调用: xtdata.get_full_tick(code_list=...)
    """
    stock_list = [s.strip() for s in stocks.split(",")]
    raw = xtdata.get_full_tick(code_list=stock_list)
    return {"data": _numpy_to_python(raw)}


@router.get("/api/sector_stocks")
def get_sector_stocks(
    sector: str = Query(..., description="板块名称，如 沪深A股"),
):
    """[旧版] 获取板块成分股。

    建议使用新版 /api/sector/stocks 替代。

    Args:
        sector: 板块名称。

    Returns:
        sector: 板块名称。
        stocks: 成分股代码列表。

    底层调用: xtdata.get_stock_list_in_sector(sector)
    """
    stock_list = xtdata.get_stock_list_in_sector(sector)
    return {"sector": sector, "stocks": stock_list}


@router.get("/api/instrument_detail")
def get_instrument_detail(
    stock: str = Query(..., description="股票代码，如 000001.SZ"),
):
    """[旧版] 获取合约详情。

    建议使用新版 /api/instrument/detail_list 替代。

    Args:
        stock: 股票代码。

    Returns:
        stock: 股票代码。
        detail: 合约详细信息。

    底层调用: xtdata.get_instrument_detail(stock)
    """
    detail = xtdata.get_instrument_detail(stock)
    return {"stock": stock, "detail": _numpy_to_python(detail)}


@router.post("/api/download")
def download_data(req: DownloadRequest):
    """[旧版] 下载单只股票的历史数据。

    建议使用新版 /api/download/history_data2 替代（支持批量下载）。

    Args:
        req.stock: 股票代码。
        req.period: K 线周期。
        req.start: 开始时间。
        req.end: 结束时间。

    Returns:
        status: 操作状态。
        stock: 股票代码。
        period: K 线周期。

    底层调用: xtdata.download_history_data(stock, period=..., start_time=..., end_time=...)
    """
    xtdata.download_history_data(
        req.stock, period=req.period, start_time=req.start, end_time=req.end
    )
    return {"status": "ok", "stock": req.stock, "period": req.period}

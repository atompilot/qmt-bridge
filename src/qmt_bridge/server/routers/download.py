"""数据下载路由模块 /api/download/*。

提供历史行情、财务数据、板块数据等的服务端下载触发端点。
底层调用 xtquant.xtdata 的下载接口，包括：
- xtdata.download_history_data2()    — 批量下载历史行情数据
- xtdata.download_financial_data()   — 下载财务报表数据
- xtdata.download_financial_data2()  — 同步下载财务数据 v2
- xtdata.download_sector_data()      — 下载板块成分数据（自动预下载）
- xtdata.download_holiday_data()     — 下载节假日日历（自动预下载）
- xtdata.download_history_contracts()— 下载历史合约（自动预下载）
- xtdata.download_index_weight()     — 下载指数权重（自动预下载）
- xtdata.download_etf_info()         — 下载 ETF 信息（自动预下载）
- xtdata.download_cb_data()          — 下载可转债数据（自动预下载）
- xtdata.download_metatable_data()   — 下载合约元数据表
- xtdata.download_his_st_data()      — 下载历史 ST 数据
- xtdata.download_tabular_data()     — 下载表格数据

其中标记为"自动预下载"的 6 个端点会由 scheduler 模块在服务启动时自动执行
一轮，之后每 24 小时定时刷新，客户端通常无需手动调用。
"""

from fastapi import APIRouter
from xtquant import xtdata

from ..downloader import download_history_data2_safe
from ..helpers import _numpy_to_python
from ..models import (
    BatchDownloadRequest,
    FinancialDownload2Request,
    FinancialDownloadRequest,
    HisSTDataDownloadRequest,
    TabularDataDownloadRequest,
)

router = APIRouter(prefix="/api/download", tags=["download"])


@router.post("/history_data2")
def download_history_data2(req: BatchDownloadRequest):
    """批量下载历史行情数据。

    向行情服务器请求下载指定股票在时间范围内的历史 K 线数据到服务端本地。
    此接口为异步操作，下载任务在服务端后台执行。可通过 WebSocket
    ``/ws/download_progress`` 端点实时跟踪下载进度。

    Args:
        req.stock_list: 股票代码列表，如 ``["000001.SZ", "600519.SH"]``。
        req.period: K 线周期，如 ``"1d"``/``"1m"``/``"5m"``。
        req.start_time: 开始时间，格式 ``"20230101"``。
        req.end_time: 结束时间，格式同上。

    Returns:
        stocks: 请求的股票代码列表。
        period: 请求的 K 线周期。
        result: 下载结果详情。

    底层调用: downloader.download_history_data2_safe() — 逐只下载，绕过 xtquant bug。
    """
    result = download_history_data2_safe(
        req.stock_list,
        period=req.period,
        start_time=req.start_time,
        end_time=req.end_time,
    )
    return {
        "status": "ok",
        "stocks": req.stock_list,
        "period": req.period,
        "result": result,
    }


@router.post("/financial_data")
def download_financial_data(req: FinancialDownloadRequest):
    """下载财务报表数据。

    触发服务端向行情服务器请求下载指定股票的财务报表数据。
    此接口为异步操作，下载任务在服务端后台执行。

    Args:
        req.stock_list: 股票代码列表。
        req.table_list: 财务表名列表，如 ``["Balance", "Income"]``。
        req.start_time: 开始时间。
        req.end_time: 结束时间。

    Returns:
        stocks: 请求的股票代码列表。
        tables: 请求的财务表名列表。

    底层调用: xtdata.download_financial_data(stock_list, table_list=..., ...)
    """
    xtdata.download_financial_data(
        req.stock_list,
        table_list=req.table_list,
        start_time=req.start_time,
        end_time=req.end_time,
    )
    return {"status": "ok", "stocks": req.stock_list, "tables": req.table_list}


@router.post("/sector_data")
def download_sector_data():
    """下载板块成分数据。

    下载全部板块（行业/概念等）的成分股数据到服务端本地。
    建议定期执行以保持板块数据最新。此接口为同步阻塞操作。

    Note:
        **自动预下载**: 此端点由 scheduler 模块在服务启动时自动执行，
        之后每 24 小时定时刷新，客户端通常无需手动调用。

    Returns:
        status: 操作状态。

    底层调用: xtdata.download_sector_data()
    """
    xtdata.download_sector_data()
    return {"status": "ok"}


@router.post("/index_weight")
def download_index_weight():
    """下载指数成分权重数据。

    下载全部指数的成分股权重数据到服务端本地。
    下载后可通过 ``/api/instrument/index_weight`` 端点查询。
    此接口为同步阻塞操作。

    Note:
        **自动预下载**: 此端点由 scheduler 模块在服务启动时自动执行，
        之后每 24 小时定时刷新，客户端通常无需手动调用。

    Returns:
        status: 操作状态。

    底层调用: xtdata.download_index_weight()
    """
    xtdata.download_index_weight()
    return {"status": "ok"}


@router.post("/etf_info")
def download_etf_info():
    """下载 ETF 申赎信息。

    下载 ETF 基金的申购赎回清单数据到服务端本地。
    下载后可通过 ``/api/etf/info`` 端点查询。此接口为同步阻塞操作。

    Note:
        **自动预下载**: 此端点由 scheduler 模块在服务启动时自动执行，
        之后每 24 小时定时刷新，客户端通常无需手动调用。

    Returns:
        status: 操作状态。

    底层调用: xtdata.download_etf_info()
    """
    xtdata.download_etf_info()
    return {"status": "ok"}


@router.post("/cb_data")
def download_cb_data():
    """下载可转债数据。

    下载全部可转债的基本信息和转股价格等数据到服务端本地。
    此接口为同步阻塞操作。

    Note:
        **自动预下载**: 此端点由 scheduler 模块在服务启动时自动执行，
        之后每 24 小时定时刷新，客户端通常无需手动调用。

    Returns:
        status: 操作状态。

    底层调用: xtdata.download_cb_data()
    """
    xtdata.download_cb_data()
    return {"status": "ok"}


@router.post("/history_contracts")
def download_history_contracts():
    """下载历史合约数据（含已到期合约）。

    下载已到期的期货/期权合约列表数据到服务端本地，用于历史数据回测。
    此接口为同步阻塞操作。

    Note:
        **自动预下载**: 此端点由 scheduler 模块在服务启动时自动执行，
        之后每 24 小时定时刷新，客户端通常无需手动调用。

    Returns:
        status: 操作状态。

    底层调用: xtdata.download_history_contracts()
    """
    xtdata.download_history_contracts()
    return {"status": "ok"}


@router.post("/financial_data2")
def download_financial_data2(req: FinancialDownload2Request):
    """同步下载财务数据 v2（阻塞直至完成）。

    与异步版本 ``download_financial_data`` 不同，此接口会阻塞等待
    下载完成后再返回结果。适用于需要确保数据就绪后再进行后续处理的场景。

    Args:
        req.stock_list: 股票代码列表。
        req.table_list: 财务表名列表，如 ``["Balance", "Income"]``，为空则下载全部。

    Returns:
        stocks: 请求的股票代码列表。
        tables: 请求的财务表名列表。

    底层调用: xtdata.download_financial_data2(stock_list, table_list=...)
    """
    xtdata.download_financial_data2(
        req.stock_list,
        table_list=req.table_list,
    )
    return {"status": "ok", "stocks": req.stock_list, "tables": req.table_list}


@router.post("/metatable_data")
def download_metatable_data():
    """下载合约元数据表（期货合约品种信息）。

    下载期货等品种的合约元数据信息表到服务端本地。此接口为同步阻塞操作。

    **重要**: 在查询期货合约列表或获取主力合约前必须先调用此端点，
    否则无法识别期货品种。

    Returns:
        status: 操作状态。

    底层调用: xtdata.download_metatable_data()
    """
    xtdata.download_metatable_data()
    return {"status": "ok"}


@router.post("/holiday_data")
def download_holiday_data():
    """下载节假日日历数据。

    下载交易所公布的节假日日历数据到服务端本地。
    此接口为同步阻塞操作。

    Note:
        **自动预下载**: 此端点由 scheduler 模块在服务启动时自动执行，
        之后每 24 小时定时刷新，客户端通常无需手动调用。

    Returns:
        status: 操作状态。

    底层调用: xtdata.download_holiday_data()
    """
    xtdata.download_holiday_data()
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# 新增下载端点
# ---------------------------------------------------------------------------


@router.post("/his_st_data")
def download_his_st_data(req: HisSTDataDownloadRequest):
    """下载历史 ST 数据。

    下载指定股票在时间范围内的历史 ST（特别处理）标记数据到服务端本地。
    此接口为异步操作，下载任务在服务端后台执行。

    Args:
        req.stock_list: 股票代码列表，如 ``["000001.SZ", "600519.SH"]``。
        req.period: K 线周期，如 ``"1d"``/``"1m"``/``"5m"``。
        req.start_time: 开始时间，格式 ``"20230101"``。
        req.end_time: 结束时间，格式同上。

    Returns:
        stocks: 请求的股票代码列表。
        result: 下载结果详情。

    底层调用: xtdata.download_his_st_data(stock_list, period=..., ...)
    """
    result = xtdata.download_his_st_data(
        req.stock_list,
        period=req.period,
        start_time=req.start_time,
        end_time=req.end_time,
    )
    return {
        "status": "ok",
        "stocks": req.stock_list,
        "result": _numpy_to_python(result) if result else {},
    }


@router.post("/tabular_data")
def download_tabular_data(req: TabularDataDownloadRequest):
    """下载表格数据。

    下载指定表名的表格数据到服务端本地。此接口为同步阻塞操作。

    Args:
        req.table_list: 需要下载的表名列表。

    Returns:
        tables: 请求的表名列表。
        result: 下载结果详情。

    底层调用: xtdata.download_tabular_data(table_list)
    """
    result = xtdata.download_tabular_data(req.table_list)
    return {
        "status": "ok",
        "tables": req.table_list,
        "result": _numpy_to_python(result) if result else {},
    }

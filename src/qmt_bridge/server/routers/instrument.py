"""合约信息路由模块 /api/instrument/*。

提供合约详情、合约类型、IPO 信息、指数权重、ST 历史等端点。
底层调用 xtquant.xtdata 的合约信息接口，包括：
- xtdata.get_instrument_detail_list()  — 批量获取合约详情
- xtdata.get_instrument_type()         — 获取合约类型
- xtdata.get_ipo_info()                — 获取新股 IPO 信息
- xtdata.get_index_weight()            — 获取指数成分股权重
- xtdata.get_his_st_data()             — 获取历史 ST 状态数据
"""

from fastapi import APIRouter, Query
from xtquant import xtdata

from ..helpers import _numpy_to_python

router = APIRouter(prefix="/api/instrument", tags=["instrument"])


@router.get("/detail_list")
def get_instrument_detail_list(
    stocks: str = Query(..., description="股票代码列表，逗号分隔"),
    iscomplete: bool = Query(False, description="是否返回完整信息"),
):
    """批量获取合约详情信息。

    Args:
        stocks: 逗号分隔的股票代码列表。
        iscomplete: 是否返回完整信息（True 返回全部字段，False 返回精简字段）。

    Returns:
        data: 合约详情字典，键为股票代码。

    底层调用: xtdata.get_instrument_detail_list(stock_list, iscomplete=...)
    """
    stock_list = [s.strip() for s in stocks.split(",")]
    raw = xtdata.get_instrument_detail_list(stock_list, iscomplete=iscomplete)
    return {"data": _numpy_to_python(raw)}


@router.get("/type")
def get_instrument_type(
    stock: str = Query(..., description="股票代码，如 600000.SH"),
):
    """获取合约类型。

    Args:
        stock: 股票代码。

    Returns:
        stock: 股票代码。
        type: 合约类型字符串（如 stock、index、fund 等）。

    底层调用: xtdata.get_instrument_type(stock)
    """
    raw = xtdata.get_instrument_type(stock)
    return {"stock": stock, "type": raw}


@router.get("/ipo_info")
def get_ipo_info(
    start_time: str = Query("", description="开始时间"),
    end_time: str = Query("", description="结束时间"),
):
    """获取新股 IPO 信息。

    Args:
        start_time: 开始时间。
        end_time: 结束时间。

    Returns:
        data: IPO 信息列表。

    底层调用: xtdata.get_ipo_info(start_time=..., end_time=...)
    """
    raw = xtdata.get_ipo_info(start_time=start_time, end_time=end_time)
    return {"data": _numpy_to_python(raw)}


@router.get("/index_weight")
def get_index_weight(
    index_code: str = Query(..., description="指数代码，如 000300.SH"),
):
    """获取指数成分股权重。

    Args:
        index_code: 指数代码，如 000300.SH（沪深300）。

    Returns:
        index_code: 指数代码。
        data: 成分股权重数据。

    底层调用: xtdata.get_index_weight(index_code)
    """
    raw = xtdata.get_index_weight(index_code)
    return {"index_code": index_code, "data": _numpy_to_python(raw)}


@router.get("/his_st_data")
def get_his_st_data(
    stock: str = Query(..., description="股票代码"),
):
    """获取股票的历史 ST 状态数据。

    返回该股票在历史上被标记 ST/*ST 的时间段信息。

    Args:
        stock: 股票代码。

    Returns:
        stock: 股票代码。
        data: 历史 ST 状态数据。

    底层调用: xtdata.get_his_st_data(stock)
    """
    raw = xtdata.get_his_st_data(stock)
    return {"stock": stock, "data": _numpy_to_python(raw)}

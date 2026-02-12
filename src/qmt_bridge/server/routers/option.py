"""期权数据路由模块 /api/option/*。

提供期权合约详情、期权链、期权列表等端点。
底层调用 xtquant.xtdata 的期权数据接口，包括：
- xtdata.get_option_detail_data()  — 获取期权合约详情
- xtdata.get_option_undl_data()    — 获取期权链（标的对应的全部期权合约）
- xtdata.get_option_list()         — 获取期权合约列表（按到期日/类型筛选）
- xtdata.get_his_option_list()     — 获取历史期权合约列表
"""

from fastapi import APIRouter, Query
from xtquant import xtdata

from ..helpers import _numpy_to_python

router = APIRouter(prefix="/api/option", tags=["option"])


@router.get("/detail")
def get_option_detail(
    option_code: str = Query(..., description="期权合约代码"),
):
    """获取期权合约详细信息。

    返回期权合约的行权价、到期日、合约乘数等详细信息。

    Args:
        option_code: 期权合约代码。

    Returns:
        option_code: 期权合约代码。
        data: 期权合约详细信息。

    底层调用: xtdata.get_option_detail_data(option_code)
    """
    raw = xtdata.get_option_detail_data(option_code)
    return {"option_code": option_code, "data": _numpy_to_python(raw)}


@router.get("/chain")
def get_option_chain(
    undl_code: str = Query(..., description="标的代码，如 000300.SH"),
):
    """获取标的对应的期权链。

    返回某标的资产（如沪深300指数）对应的全部期权合约信息。

    Args:
        undl_code: 标的资产代码。

    Returns:
        undl_code: 标的代码。
        data: 期权链数据。

    底层调用: xtdata.get_option_undl_data(undl_code)
    """
    raw = xtdata.get_option_undl_data(undl_code)
    return {"undl_code": undl_code, "data": _numpy_to_python(raw)}


@router.get("/list")
def get_option_list(
    undl_code: str = Query(..., description="标的代码，如 000300.SH"),
    dedate: str = Query(..., description="到期日"),
    opttype: str = Query("", description="期权类型"),
    isavailable: bool = Query(False, description="是否仅返回可交易合约"),
):
    """获取期权合约列表。

    按标的代码、到期日、期权类型等条件筛选期权合约。

    Args:
        undl_code: 标的资产代码。
        dedate: 到期日。
        opttype: 期权类型（认购/认沽），为空不筛选。
        isavailable: 是否仅返回当前可交易的合约。

    Returns:
        data: 符合条件的期权合约列表。

    底层调用: xtdata.get_option_list(undl_code, dedate, opttype=..., isavailavle=...)
    """
    raw = xtdata.get_option_list(undl_code, dedate, opttype=opttype, isavailavle=isavailable)
    return {"data": _numpy_to_python(raw)}


@router.get("/his_option_list")
def get_his_option_list(
    undl_code: str = Query(..., description="标的代码，如 000300.SH"),
    dedate: str = Query(..., description="历史日期"),
):
    """获取历史期权合约列表。

    查询某标的在历史某一天可交易的所有期权合约。

    Args:
        undl_code: 标的资产代码。
        dedate: 历史日期。

    Returns:
        data: 历史期权合约列表。

    底层调用: xtdata.get_his_option_list(undl_code, dedate)
    """
    raw = xtdata.get_his_option_list(undl_code, dedate)
    return {"data": _numpy_to_python(raw)}

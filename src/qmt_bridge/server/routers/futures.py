"""期货数据路由模块 /api/futures/*。

提供期货主力合约和次主力合约的查询端点。
底层调用 xtquant.xtdata 的期货接口，包括：
- xtdata.get_main_contract()      — 获取主力合约（按持仓量/成交量确定）
- xtdata.get_sec_main_contract()  — 获取次主力合约
"""

from fastapi import APIRouter, Query
from xtquant import xtdata

from ..helpers import _numpy_to_python

router = APIRouter(prefix="/api/futures", tags=["futures"])


@router.get("/main_contract")
def get_main_contract(
    code_market: str = Query(..., description="品种市场代码，如 IF.CFE"),
    start_time: str = Query("", description="开始时间"),
    end_time: str = Query("", description="结束时间"),
):
    """获取期货品种的主力合约。

    主力合约通常是持仓量或成交量最大的合约，会随时间换月切换。

    Args:
        code_market: 品种市场代码（如 IF.CFE 表示中金所的沪深300股指期货）。
        start_time: 开始时间。
        end_time: 结束时间。

    Returns:
        code_market: 品种市场代码。
        data: 主力合约代码及对应日期。

    底层调用: xtdata.get_main_contract(code_market, start_time=..., end_time=...)
    """
    raw = xtdata.get_main_contract(code_market, start_time=start_time, end_time=end_time)
    return {"code_market": code_market, "data": _numpy_to_python(raw)}


@router.get("/sec_main_contract")
def get_sec_main_contract(
    code_market: str = Query(..., description="品种市场代码，如 IF.CFE"),
    start_time: str = Query("", description="开始时间"),
    end_time: str = Query("", description="结束时间"),
):
    """获取期货品种的次主力合约。

    次主力合约通常是持仓量或成交量第二大的合约。

    Args:
        code_market: 品种市场代码。
        start_time: 开始时间。
        end_time: 结束时间。

    Returns:
        code_market: 品种市场代码。
        data: 次主力合约代码及对应日期。

    底层调用: xtdata.get_sec_main_contract(code_market, start_time=..., end_time=...)
    """
    raw = xtdata.get_sec_main_contract(code_market, start_time=start_time, end_time=end_time)
    return {"code_market": code_market, "data": _numpy_to_python(raw)}

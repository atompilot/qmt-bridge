"""Router — Hong Kong market endpoints /api/hk/*."""

from fastapi import APIRouter, Query
from xtquant import xtdata

from ..helpers import _numpy_to_python

router = APIRouter(prefix="/api/hk", tags=["hk"])


@router.get("/stock_list")
def get_hk_stock_list():
    """Get list of HK-connected stocks (港股通)."""
    stock_list = xtdata.get_stock_list_in_sector("沪港通") + xtdata.get_stock_list_in_sector("深港通")
    return {"count": len(stock_list), "stocks": stock_list}


@router.get("/connect_stocks")
def get_hk_connect_stocks(
    connect_type: str = Query("north", description="通道类型: north(北向)/south(南向)"),
):
    """Get HK-connect stock list by direction."""
    if connect_type == "south":
        stock_list = xtdata.get_stock_list_in_sector("港股通")
    else:
        stock_list = xtdata.get_stock_list_in_sector("沪股通") + xtdata.get_stock_list_in_sector("深股通")
    return {"connect_type": connect_type, "count": len(stock_list), "stocks": stock_list}

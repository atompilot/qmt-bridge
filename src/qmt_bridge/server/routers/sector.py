"""Router — Sector endpoints /api/sector/*."""

from fastapi import APIRouter, Query
from xtquant import xtdata

from ..helpers import _numpy_to_python
from ..models import (
    AddSectorStocksRequest,
    CreateSectorFolderRequest,
    CreateSectorRequest,
    RemoveSectorStocksRequest,
    ResetSectorRequest,
)

router = APIRouter(prefix="/api/sector", tags=["sector"])


@router.get("/list")
def get_sector_list():
    sectors = xtdata.get_sector_list()
    return {"sectors": sectors}


@router.get("/stocks")
def get_sector_stocks(
    sector: str = Query(..., description="板块名称，如 沪深A股 / 上证A股 / 深证A股 / 沪深ETF / 上证50 / 沪深300"),
    real_timetag: int = Query(-1, description="历史日期时间戳（毫秒），-1 表示最新"),
):
    stock_list = xtdata.get_stock_list_in_sector(sector, real_timetag=real_timetag)
    return {"sector": sector, "count": len(stock_list), "stocks": stock_list}


@router.get("/info")
def get_sector_info(
    sector: str = Query("", description="板块名称，为空返回所有板块信息"),
):
    raw = xtdata.get_sector_info(sector_name=sector)
    return {"data": _numpy_to_python(raw)}


# ---------------------------------------------------------------------------
# Write operations (Step 5)
# ---------------------------------------------------------------------------


@router.post("/create_folder")
def create_sector_folder(req: CreateSectorFolderRequest):
    """Create a new sector folder."""
    result = xtdata.create_sector_folder(req.folder_name)
    return {"status": "ok", "data": _numpy_to_python(result)}


@router.post("/create")
def create_sector(req: CreateSectorRequest):
    """Create a new sector under a folder."""
    result = xtdata.create_sector(req.sector_name, req.parent_node)
    return {"status": "ok", "data": _numpy_to_python(result)}


@router.post("/add_stocks")
def add_sector_stocks(req: AddSectorStocksRequest):
    """Add stocks to a sector."""
    result = xtdata.add_sector(req.sector_name, req.stocks)
    return {"status": "ok", "data": _numpy_to_python(result)}


@router.post("/remove_stocks")
def remove_sector_stocks(req: RemoveSectorStocksRequest):
    """Remove stocks from a sector."""
    result = xtdata.remove_stock_from_sector(req.sector_name, req.stocks)
    return {"status": "ok", "data": _numpy_to_python(result)}


@router.delete("/remove")
def remove_sector(
    sector_name: str = Query(..., description="板块名称"),
):
    """Remove an entire sector."""
    result = xtdata.remove_sector(sector_name)
    return {"status": "ok", "data": _numpy_to_python(result)}


@router.post("/reset")
def reset_sector(req: ResetSectorRequest):
    """Reset sector stocks (replace all stocks)."""
    result = xtdata.reset_sector(req.sector_name, req.stocks)
    return {"status": "ok", "data": _numpy_to_python(result)}

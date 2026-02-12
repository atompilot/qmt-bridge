"""板块管理路由模块 /api/sector/*。

提供板块的查询、创建、删除及成分股增删改查等端点。
底层调用 xtquant.xtdata 的板块管理接口，包括：
- xtdata.get_sector_list()              — 获取全部板块列表
- xtdata.get_stock_list_in_sector()     — 获取板块成分股列表
- xtdata.get_sector_info()              — 获取板块详细信息
- xtdata.create_sector_folder()         — 创建板块文件夹
- xtdata.create_sector()                — 创建板块
- xtdata.add_sector()                   — 向板块添加成分股
- xtdata.remove_stock_from_sector()     — 从板块移除成分股
- xtdata.remove_sector()                — 删除板块
- xtdata.reset_sector()                 — 重置板块成分股（替换全部）
"""

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
    """获取所有板块名称列表。

    Returns:
        sectors: 所有板块名称的字符串列表。

    底层调用: xtdata.get_sector_list()
    """
    sectors = xtdata.get_sector_list()
    return {"sectors": sectors}


@router.get("/stocks")
def get_sector_stocks(
    sector: str = Query(..., description="板块名称，如 沪深A股 / 上证A股 / 深证A股 / 沪深ETF / 上证50 / 沪深300"),
    real_timetag: int = Query(-1, description="历史日期时间戳（毫秒），-1 表示最新"),
):
    """获取指定板块的成分股列表。

    Args:
        sector: 板块名称，如 "沪深A股"、"上证50"。
        real_timetag: 历史日期的毫秒时间戳，-1 表示获取最新成分股。

    Returns:
        sector: 板块名称。
        count: 成分股数量。
        stocks: 成分股代码列表。

    底层调用: xtdata.get_stock_list_in_sector(sector, real_timetag=...)
    """
    stock_list = xtdata.get_stock_list_in_sector(sector, real_timetag=real_timetag)
    return {"sector": sector, "count": len(stock_list), "stocks": stock_list}


@router.get("/info")
def get_sector_info(
    sector: str = Query("", description="板块名称，为空返回所有板块信息"),
):
    """获取板块详细信息。

    Args:
        sector: 板块名称，为空时返回所有板块的信息。

    Returns:
        data: 板块详细信息字典。

    底层调用: xtdata.get_sector_info(sector_name=...)
    """
    try:
        raw = xtdata.get_sector_info(sector_name=sector)
    except FileNotFoundError:
        # 板块不存在时返回空字典
        return {"data": {}}
    return {"data": _numpy_to_python(raw)}


# ---------------------------------------------------------------------------
# 板块写操作端点
# ---------------------------------------------------------------------------


@router.post("/create_folder")
def create_sector_folder(req: CreateSectorFolderRequest):
    """创建新的板块文件夹。

    Args:
        req.folder_name: 文件夹名称。

    Returns:
        操作结果。

    底层调用: xtdata.create_sector_folder(folder_name)
    """
    result = xtdata.create_sector_folder(req.folder_name)
    return {"status": "ok", "data": _numpy_to_python(result)}


@router.post("/create")
def create_sector(req: CreateSectorRequest):
    """在指定文件夹下创建新板块。

    Args:
        req.sector_name: 板块名称。
        req.parent_node: 父节点（文件夹名称）。

    Returns:
        操作结果。

    底层调用: xtdata.create_sector(sector_name, parent_node)
    """
    result = xtdata.create_sector(req.sector_name, req.parent_node)
    return {"status": "ok", "data": _numpy_to_python(result)}


@router.post("/add_stocks")
def add_sector_stocks(req: AddSectorStocksRequest):
    """向板块添加成分股。

    Args:
        req.sector_name: 板块名称。
        req.stocks: 要添加的股票代码列表。

    Returns:
        操作结果。

    底层调用: xtdata.add_sector(sector_name, stocks)
    """
    result = xtdata.add_sector(req.sector_name, req.stock_list)
    return {"status": "ok", "data": _numpy_to_python(result)}


@router.post("/remove_stocks")
def remove_sector_stocks(req: RemoveSectorStocksRequest):
    """从板块中移除指定成分股。

    Args:
        req.sector_name: 板块名称。
        req.stocks: 要移除的股票代码列表。

    Returns:
        操作结果。

    底层调用: xtdata.remove_stock_from_sector(sector_name, stocks)
    """
    result = xtdata.remove_stock_from_sector(req.sector_name, req.stock_list)
    return {"status": "ok", "data": _numpy_to_python(result)}


@router.delete("/remove")
def remove_sector(
    sector_name: str = Query(..., description="板块名称"),
):
    """删除整个板块。

    Args:
        sector_name: 要删除的板块名称。

    Returns:
        操作结果。

    底层调用: xtdata.remove_sector(sector_name)
    """
    result = xtdata.remove_sector(sector_name)
    return {"status": "ok", "data": _numpy_to_python(result)}


@router.post("/reset")
def reset_sector(req: ResetSectorRequest):
    """重置板块成分股（用新的股票列表替换全部现有成分股）。

    Args:
        req.sector_name: 板块名称。
        req.stocks: 新的成分股代码列表（将替换板块中所有现有股票）。

    Returns:
        操作结果。

    底层调用: xtdata.reset_sector(sector_name, stocks)
    """
    result = xtdata.reset_sector(req.sector_name, req.stock_list)
    return {"status": "ok", "data": _numpy_to_python(result)}

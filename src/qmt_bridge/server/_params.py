"""参数解析依赖模块。

提供 FastAPI 依赖注入函数，支持 xtquant 原生参数命名（如 stock_code）
和简写别名（如 stock）共存，实现向后兼容。
"""

from fastapi import HTTPException, Query


def stock_code_param(
    stock_code: str | None = Query(None, description="股票代码"),
    stock: str | None = Query(None, description="股票代码（别名）"),
) -> str:
    """解析单只股票代码参数，支持 stock_code 和 stock 两种命名。"""
    value = stock_code or stock
    if not value:
        raise HTTPException(status_code=422, detail="stock_code or stock is required")
    return value


def stock_list_param(
    stock_list: str | None = Query(None, description="股票代码列表，逗号分隔"),
    stocks: str | None = Query(None, description="股票代码列表（别名），逗号分隔"),
) -> list[str]:
    """解析股票代码列表参数，支持 stock_list 和 stocks 两种命名。"""
    raw = stock_list or stocks
    if not raw:
        return []
    return [s.strip() for s in raw.split(",") if s.strip()]


def field_list_param(
    field_list: str | None = Query(None, description="字段列表，逗号分隔"),
    fields: str | None = Query(None, description="字段列表（别名），逗号分隔"),
) -> list[str]:
    """解析字段列表参数，支持 field_list 和 fields 两种命名。"""
    raw = field_list or fields
    if not raw:
        return []
    return [f.strip() for f in raw.split(",") if f.strip()]


def table_list_param(
    table_list: str | None = Query(None, description="表名列表，逗号分隔"),
    tables: str | None = Query(None, description="表名列表（别名），逗号分隔"),
) -> list[str]:
    """解析表名列表参数，支持 table_list 和 tables 两种命名。"""
    raw = table_list or tables
    if not raw:
        return []
    return [t.strip() for t in raw.split(",") if t.strip()]


def sector_name_param(
    sector_name: str | None = Query(None, description="板块名称"),
    sector: str | None = Query(None, description="板块名称（别名）"),
) -> str:
    """解析板块名称参数，支持 sector_name 和 sector 两种命名。"""
    value = sector_name or sector
    if not value:
        raise HTTPException(status_code=422, detail="sector_name or sector is required")
    return value

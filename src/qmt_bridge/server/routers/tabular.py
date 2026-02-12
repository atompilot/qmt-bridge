"""表格数据路由模块 /api/tabular/*。

提供通用表格数据的查询端点，可用于查询各种命名数据表。
底层调用 xtquant.xtdata 的数据接口，包括：
- xtdata.get_financial_data()      — 按表名获取表格数据
- xtdata.get_financial_table_list() — 获取可用数据表列表
"""

from fastapi import APIRouter, Query
from xtquant import xtdata

from ..helpers import _numpy_to_python

router = APIRouter(prefix="/api/tabular", tags=["tabular"])


@router.get("/data")
def get_tabular_data(
    table_name: str = Query(..., description="表名"),
    stocks: str = Query("", description="股票代码列表，逗号分隔"),
    start_time: str = Query("", description="开始时间"),
    end_time: str = Query("", description="结束时间"),
):
    """按表名查询表格数据。

    通用数据查询接口，通过指定表名查询对应的结构化数据。

    Args:
        table_name: 数据表名称。
        stocks: 逗号分隔的股票代码列表，为空查询全部。
        start_time: 开始时间。
        end_time: 结束时间。

    Returns:
        table: 查询的表名。
        data: 表格数据。

    底层调用: xtdata.get_financial_data(stock_list, table_list=[table_name], ...)
    """
    # 将逗号分隔的代码字符串解析为列表，为空则传空列表
    stock_list = [s.strip() for s in stocks.split(",") if s.strip()] if stocks else []
    raw = xtdata.get_financial_data(stock_list, table_list=[table_name], start_time=start_time, end_time=end_time)
    return {"table": table_name, "data": _numpy_to_python(raw)}


@router.get("/tables")
def list_tables():
    """列出所有可用的数据表名称。

    Returns:
        tables: 可用数据表名称列表。

    底层调用: xtdata.get_financial_table_list()
    """
    try:
        tables = xtdata.get_financial_table_list()
        return {"tables": _numpy_to_python(tables)}
    except Exception:
        # 接口不可用时返回空列表
        return {"tables": []}


@router.get("/formula")
def get_tabular_formula(
    table_name: str = Query(..., description="表名"),
    stocks: str = Query("", description="股票代码列表，逗号分隔"),
    start_time: str = Query("", description="开始时间"),
    end_time: str = Query("", description="结束时间"),
):
    """按表名查询公式表格数据 → xtdata.get_tabular_formula()"""
    stock_list = [s.strip() for s in stocks.split(",") if s.strip()] if stocks else []
    raw = xtdata.get_tabular_formula(stock_list, table_name=table_name, start_time=start_time, end_time=end_time)
    return {"table": table_name, "data": _numpy_to_python(raw)}

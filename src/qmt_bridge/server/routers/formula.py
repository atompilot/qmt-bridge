"""公式计算路由模块 /api/formula/*。

提供技术指标公式调用、批量计算、自定义指数生成等端点。
新增公式管理端点（create / import / delete / list）。
"""

from fastapi import APIRouter, Query
from xtquant import xtdata

from ..helpers import _numpy_to_python, ok_response
from ..models import (
    CallFormulaBatchRequest,
    CallFormulaRequest,
    CreateFormulaRequest,
    GenerateIndexDataRequest,
    ImportFormulaRequest,
)

router = APIRouter(prefix="/api/formula", tags=["formula"])


@router.post("/call")
def call_formula(req: CallFormulaRequest):
    """对单只股票调用公式计算 → xtdata.call_formula()"""
    result = xtdata.call_formula(
        req.formula_name,
        req.stock_code,
        req.period,
        req.start_time,
        req.end_time,
        req.count,
        req.dividend_type,
        **req.params,
    )
    return {"data": _numpy_to_python(result)}


@router.post("/call_batch")
def call_formula_batch(req: CallFormulaBatchRequest):
    """对多只股票批量调用公式计算 → xtdata.call_formula_batch()"""
    result = xtdata.call_formula_batch(
        req.formula_name,
        req.stock_codes,
        req.period,
        req.start_time,
        req.end_time,
        req.count,
        req.dividend_type,
        **req.params,
    )
    return {"data": _numpy_to_python(result)}


@router.post("/generate_index_data")
def generate_index_data(req: GenerateIndexDataRequest):
    """生成自定义指数数据 → xtdata.generate_index_data()"""
    result = xtdata.generate_index_data(
        req.index_code,
        req.stock_list,
        req.weights,
        req.period,
        req.start_time,
        req.end_time,
    )
    return {"data": _numpy_to_python(result)}


# ---------------------------------------------------------------------------
# 公式管理端点（新增）
# ---------------------------------------------------------------------------


@router.post("/create")
def create_formula(req: CreateFormulaRequest):
    """创建公式 → xtdata.create_formula()"""
    result = xtdata.create_formula(req.formula_name, req.formula_file, req.formula_type)
    return ok_response(_numpy_to_python(result))


@router.post("/import")
def import_formula(req: ImportFormulaRequest):
    """导入公式 → xtdata.import_formula()"""
    result = xtdata.import_formula(req.formula_file)
    return ok_response(_numpy_to_python(result))


@router.delete("/delete")
def del_formula(
    formula_name: str = Query(..., description="公式名称"),
):
    """删除公式 → xtdata.del_formula()"""
    result = xtdata.del_formula(formula_name)
    return ok_response(_numpy_to_python(result))


@router.get("/list")
def get_formulas():
    """获取公式列表 → xtdata.get_formulas()"""
    result = xtdata.get_formulas()
    return ok_response(_numpy_to_python(result))

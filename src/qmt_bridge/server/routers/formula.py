"""Router — Formula/Model API endpoints /api/formula/*."""

from fastapi import APIRouter
from xtquant import xtdata

from ..helpers import _numpy_to_python
from ..models import (
    CallFormulaBatchRequest,
    CallFormulaRequest,
    GenerateIndexDataRequest,
)

router = APIRouter(prefix="/api/formula", tags=["formula"])


@router.post("/call")
def call_formula(req: CallFormulaRequest):
    """Call a formula/indicator on a single stock."""
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
    """Call a formula/indicator on multiple stocks."""
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


@router.post("/generate_index")
def generate_index_data(req: GenerateIndexDataRequest):
    """Generate custom index data from stocks and weights."""
    result = xtdata.generate_index_data(
        req.index_code,
        req.stocks,
        req.weights,
        req.period,
        req.start_time,
        req.end_time,
    )
    return {"data": _numpy_to_python(result)}

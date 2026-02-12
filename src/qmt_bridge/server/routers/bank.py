"""银证转账路由模块 /api/bank/*（需要 API Key 认证）。

对齐 xttrader 真实银证转账 API：
- bank_transfer_in / bank_transfer_out（同步/异步）
- query_bank_info — 查询绑定银行
- query_bank_amount — 查询银行余额（POST，含密码）
- query_bank_transfer_stream — 查询转账流水
"""

from fastapi import APIRouter, Depends, Query

from ..deps import get_trader_manager
from ..helpers import _numpy_to_python, ok_response
from ..models import BankAmountQueryRequest, BankTransferRequest, BankTransferStreamRequest
from ..security import require_api_key

router = APIRouter(prefix="/api/bank", tags=["bank"], dependencies=[Depends(require_api_key)])


@router.post("/transfer_in")
def bank_transfer_in(req: BankTransferRequest, manager=Depends(get_trader_manager)):
    """银行转证券 → manager.bank_transfer_in()"""
    result = manager.bank_transfer_in(
        bank_no=req.bank_no,
        bank_account=req.bank_account,
        balance=req.balance,
        bank_pwd=req.bank_pwd,
        fund_pwd=req.fund_pwd,
        account_id=req.account_id,
    )
    return ok_response(_numpy_to_python(result))


@router.post("/transfer_out")
def bank_transfer_out(req: BankTransferRequest, manager=Depends(get_trader_manager)):
    """证券转银行 → manager.bank_transfer_out()"""
    result = manager.bank_transfer_out(
        bank_no=req.bank_no,
        bank_account=req.bank_account,
        balance=req.balance,
        bank_pwd=req.bank_pwd,
        fund_pwd=req.fund_pwd,
        account_id=req.account_id,
    )
    return ok_response(_numpy_to_python(result))


@router.post("/transfer_in_async")
def bank_transfer_in_async(req: BankTransferRequest, manager=Depends(get_trader_manager)):
    """异步银行转证券 → manager.bank_transfer_in_async()"""
    result = manager.bank_transfer_in_async(
        bank_no=req.bank_no,
        bank_account=req.bank_account,
        balance=req.balance,
        bank_pwd=req.bank_pwd,
        fund_pwd=req.fund_pwd,
        account_id=req.account_id,
    )
    return ok_response(_numpy_to_python(result))


@router.post("/transfer_out_async")
def bank_transfer_out_async(req: BankTransferRequest, manager=Depends(get_trader_manager)):
    """异步证券转银行 → manager.bank_transfer_out_async()"""
    result = manager.bank_transfer_out_async(
        bank_no=req.bank_no,
        bank_account=req.bank_account,
        balance=req.balance,
        bank_pwd=req.bank_pwd,
        fund_pwd=req.fund_pwd,
        account_id=req.account_id,
    )
    return ok_response(_numpy_to_python(result))


@router.get("/info")
def query_bank_info(
    account_id: str = Query("", description="交易账户 ID"),
    manager=Depends(get_trader_manager),
):
    """查询绑定银行信息 → manager.query_bank_info()"""
    result = manager.query_bank_info(account_id=account_id)
    return ok_response(_numpy_to_python(result))


@router.post("/amount")
def query_bank_amount(req: BankAmountQueryRequest, manager=Depends(get_trader_manager)):
    """查询银行余额（POST 因含密码）→ manager.query_bank_amount()"""
    result = manager.query_bank_amount(
        bank_no=req.bank_no,
        bank_account=req.bank_account,
        bank_pwd=req.bank_pwd,
        account_id=req.account_id,
    )
    return ok_response(_numpy_to_python(result))


@router.get("/transfer_stream")
def query_bank_transfer_stream(
    start_date: str = Query(..., description="开始日期"),
    end_date: str = Query(..., description="结束日期"),
    bank_no: str = Query("", description="银行编号"),
    bank_account: str = Query("", description="银行账号"),
    account_id: str = Query("", description="交易账户 ID"),
    manager=Depends(get_trader_manager),
):
    """查询银证转账流水 → manager.query_bank_transfer_stream()"""
    result = manager.query_bank_transfer_stream(
        start_date=start_date,
        end_date=end_date,
        bank_no=bank_no,
        bank_account=bank_account,
        account_id=account_id,
    )
    return ok_response(_numpy_to_python(result))

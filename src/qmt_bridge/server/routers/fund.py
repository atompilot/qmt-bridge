"""资金划转路由模块 /api/fund/*（需要 API Key 认证）。

对齐 xttrader 真实资金划转 API：
- fund_transfer — 账户间资金划转
- ctp_transfer_option_to_future — 期权→期货（需要双账户 ID）
- ctp_transfer_future_to_option — 期货→期权（需要双账户 ID）
- secu_transfer — 证券划转
"""

from fastapi import APIRouter, Depends

from ..deps import get_trader_manager
from ..helpers import _numpy_to_python, ok_response
from ..models import CTPCrossMarketTransferRequest, FundTransferRequest, SecuTransferRequest
from ..security import require_api_key

router = APIRouter(prefix="/api/fund", tags=["fund"], dependencies=[Depends(require_api_key)])


@router.post("/transfer")
def fund_transfer(req: FundTransferRequest, manager=Depends(get_trader_manager)):
    """账户间资金划转 → manager.fund_transfer()"""
    result = manager.fund_transfer(
        transfer_direction=req.transfer_direction,
        amount=req.amount,
        account_id=req.account_id,
    )
    return ok_response(_numpy_to_python(result))


@router.post("/ctp_option_to_future")
def ctp_transfer_option_to_future(
    req: CTPCrossMarketTransferRequest,
    manager=Depends(get_trader_manager),
):
    """期权→期货 跨市场资金划转 → manager.ctp_transfer_option_to_future()"""
    result = manager.ctp_transfer_option_to_future(
        opt_account_id=req.opt_account_id,
        ft_account_id=req.ft_account_id,
        balance=req.balance,
    )
    return ok_response(_numpy_to_python(result))


@router.post("/ctp_future_to_option")
def ctp_transfer_future_to_option(
    req: CTPCrossMarketTransferRequest,
    manager=Depends(get_trader_manager),
):
    """期货→期权 跨市场资金划转 → manager.ctp_transfer_future_to_option()"""
    result = manager.ctp_transfer_future_to_option(
        opt_account_id=req.opt_account_id,
        ft_account_id=req.ft_account_id,
        balance=req.balance,
    )
    return ok_response(_numpy_to_python(result))


@router.post("/secu_transfer")
def secu_transfer(req: SecuTransferRequest, manager=Depends(get_trader_manager)):
    """证券划转 → manager.secu_transfer()"""
    result = manager.secu_transfer(
        transfer_direction=req.transfer_direction,
        stock_code=req.stock_code,
        volume=req.volume,
        transfer_type=req.transfer_type,
        account_id=req.account_id,
    )
    return ok_response(_numpy_to_python(result))

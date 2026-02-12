"""FastAPI 依赖注入辅助模块。

本模块定义了 FastAPI 路由中通过 ``Depends()`` 使用的依赖函数。
主要用于从 ``app.state`` 中获取在应用启动阶段（lifespan）初始化的共享对象，
例如 XtTraderManager（xttrader 交易管理器）。

使用示例::

    @router.post("/order")
    async def place_order(
        manager = Depends(get_trader_manager),
    ):
        # manager 即为 XtTraderManager 实例
        ...
"""

from fastapi import Depends, HTTPException, Request, status

from .config import Settings, get_settings


def get_trader_manager(request: Request):
    """从 app.state 获取 XtTraderManager 交易管理器实例。

    XtTraderManager 在应用启动阶段（_lifespan）初始化并存储到 app.state 中，
    它封装了 xtquant.xttrader 的连接管理、委托下单、撤单、查询等功能。

    该依赖函数用于交易相关路由，确保交易模块已启用且连接正常。
    若交易模块未启用（trader_manager 为 None），则返回 503 错误。

    Args:
        request: FastAPI 请求对象，用于访问 app.state。

    Returns:
        XtTraderManager 实例，可调用其 place_order / cancel_order 等方法。

    Raises:
        HTTPException: 503 状态码 —— 交易模块未启用或初始化失败。
    """
    manager = getattr(request.app.state, "trader_manager", None)
    if manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Trading module is not enabled",
        )
    return manager

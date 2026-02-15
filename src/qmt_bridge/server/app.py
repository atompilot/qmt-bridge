"""FastAPI 应用工厂与生命周期管理模块。

本模块负责：
1. 创建和配置 FastAPI 应用实例（应用工厂模式）
2. 管理应用生命周期（lifespan），包括：
   - 启动时初始化 xttrader 交易管理器（XtTraderManager）
   - 启动时初始化通知模块（飞书/Webhook 通知）
   - 关闭时清理所有资源连接
3. 注册所有 HTTP 路由和 WebSocket 端点

注：定时下载调度器已拆分为独立进程 ``qmt-scheduler``，
不再随 API 服务启动，避免 xtdata C 扩展并发调用崩溃。
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from .config import Settings, get_settings

# 全局日志记录器，用于记录服务端运行状态
logger = logging.getLogger("qmt_bridge")

# ── xtdata 并发保护 ─────────────────────────────────────────────
# xtdata 的 C 扩展不是线程安全的。FastAPI 把同步路由处理函数分发到
# 线程池并发执行，多个请求同时调用 xtdata 会导致 BSON 断言崩溃。
#
# 用 asyncio.Lock 包装的 async generator 依赖：
#   1. 事件循环中 acquire —— 排队等候
#   2. yield —— FastAPI 把 sync handler 提交到线程池并 await
#   3. handler 完成后回到事件循环 release
# 效果：同一时刻最多一个 sync handler 在线程池里调用 xtdata。
# ────────────────────────────────────────────────────────────────

_xtdata_lock = asyncio.Lock()


async def _xtdata_serialize():
    """FastAPI 依赖：串行化 xtdata 调用，防止并发导致 C 扩展崩溃。"""
    logger.debug("xtdata_lock: 等待获取锁...")
    async with _xtdata_lock:
        logger.debug("xtdata_lock: ✓ 已获取锁")
        yield
    logger.debug("xtdata_lock: 已释放锁")


# 所有调用 xtdata 的 HTTP 路由共享此依赖列表
_serial = [Depends(_xtdata_serialize)]


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """管理 FastAPI 应用的生命周期（启动/关闭）。

    启动阶段（yield 之前）：
    1. 若启用交易功能，初始化 XtTraderManager 并连接 miniQMT 客户端
    2. 若启用通知功能，启动 NotifierManager（飞书/Webhook 通知后端）

    关闭阶段（yield 之后）：
    1. 停止通知模块
    2. 断开交易管理器连接（底层调用 xttrader.disconnect()）

    Args:
        app: FastAPI 应用实例，通过 app.state 存储共享状态
    """
    settings: Settings = get_settings()

    # 如果配置中启用了交易模块，则初始化 xttrader 交易管理器
    if settings.trading_enabled:
        try:
            from .trading.manager import XtTraderManager

            # 创建交易管理器实例，传入 miniQMT 安装路径和资金账号
            manager = XtTraderManager(
                mini_qmt_path=settings.mini_qmt_path,
                account_id=settings.trading_account_id,
            )
            # 连接到 miniQMT 客户端（底层调用 xttrader.connect()）
            manager.connect()
            # 将管理器存储到 app.state，供各路由通过依赖注入获取
            app.state.trader_manager = manager
            logger.info("Trading module initialized")
        except Exception:
            logger.exception("Failed to initialize trading module")
            app.state.trader_manager = None
    else:
        app.state.trader_manager = None

    # 初始化通知模块（独立于交易模块，可单独启用）
    if settings.notify_enabled:
        try:
            from .notify import NotifierManager

            # 创建通知管理器并启动后台任务
            notifier = NotifierManager(settings)
            await notifier.start()
            app.state.notifier_manager = notifier
            logger.info("Notification module initialized")

            # 如果交易模块也已启用，将通知器注入到交易回调中
            # 这样当 xttrader 产生委托/成交回调时，可自动推送通知
            manager = getattr(app.state, "trader_manager", None)
            if manager is not None and hasattr(manager, "_callback"):
                manager._callback.set_notifier(notifier)
        except Exception:
            logger.exception("Failed to initialize notification module")
            app.state.notifier_manager = None
    else:
        app.state.notifier_manager = None

    yield  # --- 应用运行中，以下为关闭阶段 ---

    # 停止通知模块，释放后台资源
    notifier = getattr(app.state, "notifier_manager", None)
    if notifier is not None:
        try:
            await notifier.stop()
            logger.info("Notification module stopped")
        except Exception:
            logger.exception("Error stopping notification module")

    # 断开交易管理器连接（底层调用 xttrader.disconnect()）
    manager = getattr(app.state, "trader_manager", None)
    if manager is not None:
        try:
            manager.disconnect()
            logger.info("Trading module disconnected")
        except Exception:
            logger.exception("Error disconnecting trading module")


def create_app(settings: Settings | None = None) -> FastAPI:
    """创建并配置 FastAPI 应用实例（应用工厂函数）。

    该函数完成以下工作：
    1. 创建 FastAPI 实例并绑定生命周期管理器
    2. 注册所有数据查询路由（行情、板块、财务等，始终可用）
    3. 注册 WebSocket 端点（实时行情推送、下载进度等）
    4. 根据配置条件注册通知路由和交易路由

    Args:
        settings: 应用配置对象。若为 None，则从环境变量自动加载。

    Returns:
        配置完成的 FastAPI 应用实例，可直接传给 uvicorn 运行。
    """
    if settings is None:
        settings = get_settings()

    app = FastAPI(
        title="QMT Bridge",
        description="miniQMT market data & trading API bridge",
        version="2.0.0",
        lifespan=_lifespan,
    )

    # ------------------------------------------------------------------
    # 注册数据查询路由（始终可用，无需启用交易模块）
    # 这些路由底层调用 xtquant.xtdata 的各类行情数据接口
    # dependencies=_serial 确保同一时刻只有一个请求调用 xtdata
    # ------------------------------------------------------------------
    from .routers import (
        calendar,
        cb,
        download,
        etf,
        financial,
        formula,
        futures,
        hk,
        instrument,
        legacy,
        market,
        meta,
        option,
        sector,
        tabular,
        tick,
        utility,
    )

    app.include_router(market.router, dependencies=_serial)
    app.include_router(tick.router, dependencies=_serial)
    app.include_router(sector.router, dependencies=_serial)
    app.include_router(calendar.router, dependencies=_serial)
    app.include_router(financial.router, dependencies=_serial)
    app.include_router(instrument.router, dependencies=_serial)
    app.include_router(option.router, dependencies=_serial)
    app.include_router(etf.router, dependencies=_serial)
    app.include_router(cb.router, dependencies=_serial)
    app.include_router(futures.router, dependencies=_serial)
    app.include_router(meta.router, dependencies=_serial)
    app.include_router(download.router, dependencies=_serial)
    app.include_router(formula.router, dependencies=_serial)
    app.include_router(hk.router, dependencies=_serial)
    app.include_router(tabular.router, dependencies=_serial)
    app.include_router(utility.router, dependencies=_serial)
    app.include_router(legacy.router, dependencies=_serial)

    # ------------------------------------------------------------------
    # 注册 WebSocket 端点（实时数据推送）
    # WebSocket 不加串行化依赖，避免长连接永久持锁
    # ------------------------------------------------------------------
    from .ws import download_progress, formula as formula_ws, realtime, whole_quote

    app.include_router(realtime.router)
    app.include_router(whole_quote.router)
    app.include_router(download_progress.router)
    app.include_router(formula_ws.router)

    # ------------------------------------------------------------------
    # 注册通知路由（仅在配置中启用通知时加载）
    # ------------------------------------------------------------------
    if settings.notify_enabled:
        from .notify.base import router as notify_router

        app.include_router(notify_router)  # 通知管理接口

    # ------------------------------------------------------------------
    # 注册交易路由（仅在配置中启用交易时加载）
    # 这些路由底层调用 xtquant.xttrader 的交易接口
    # ------------------------------------------------------------------
    if settings.trading_enabled:
        from .routers import bank, credit, fund, smt, trading

        app.include_router(trading.router, dependencies=_serial)
        app.include_router(credit.router, dependencies=_serial)
        app.include_router(fund.router, dependencies=_serial)
        app.include_router(smt.router, dependencies=_serial)
        app.include_router(bank.router, dependencies=_serial)

        from .ws import trade_callback

        app.include_router(trade_callback.router)

    return app

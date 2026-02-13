"""FastAPI 应用工厂与生命周期管理模块。

本模块负责：
1. 创建和配置 FastAPI 应用实例（应用工厂模式）
2. 管理应用生命周期（lifespan），包括：
   - 启动时初始化 xttrader 交易管理器（XtTraderManager）
   - 启动时初始化通知模块（飞书/Webhook 通知）
   - 启动后台数据预下载调度器
   - 关闭时清理所有资源连接
3. 注册所有 HTTP 路由和 WebSocket 端点
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .config import Settings, get_settings

# 全局日志记录器，用于记录服务端运行状态
logger = logging.getLogger("qmt_bridge")


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """管理 FastAPI 应用的生命周期（启动/关闭）。

    启动阶段（yield 之前）：
    1. 若启用交易功能，初始化 XtTraderManager 并连接 miniQMT 客户端
       （底层调用 xttrader.connect() 建立与 miniQMT 的通信连接）
    2. 若启用通知功能，启动 NotifierManager（飞书/Webhook 通知后端）
    3. 启动后台数据预下载调度器（scheduler_loop），定时调用 xtdata 下载数据

    关闭阶段（yield 之后）：
    1. 取消后台调度任务
    2. 停止通知模块
    3. 断开交易管理器连接（底层调用 xttrader.disconnect()）

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

    # 启动后台数据预下载调度器（定时调用 xtdata 下载行情数据）
    from .downloader import DownloadSchedulerState
    from .scheduler import scheduler_loop

    download_scheduler_state = DownloadSchedulerState()
    app.state.download_scheduler = download_scheduler_state

    scheduler_task = asyncio.create_task(
        scheduler_loop(download_scheduler_state, settings)
    )
    app.state.scheduler_task = scheduler_task

    yield  # --- 应用运行中，以下为关闭阶段 ---

    # 取消后台调度任务
    scheduler_task = getattr(app.state, "scheduler_task", None)
    if scheduler_task:
        scheduler_task.cancel()

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

    app.include_router(market.router)       # K线行情数据路由
    app.include_router(tick.router)         # 逐笔成交/分笔数据路由
    app.include_router(sector.router)       # 板块分类与成分股路由
    app.include_router(calendar.router)     # 交易日历路由
    app.include_router(financial.router)    # 财务数据路由
    app.include_router(instrument.router)   # 合约基础信息路由
    app.include_router(option.router)       # 期权数据路由
    app.include_router(etf.router)          # ETF 相关数据路由
    app.include_router(cb.router)           # 可转债相关数据路由
    app.include_router(futures.router)      # 期货数据路由
    app.include_router(meta.router)         # 元数据/合约信息表路由
    app.include_router(download.router)     # 数据下载（触发 xtdata 本地缓存）路由
    app.include_router(formula.router)      # 公式/模型计算路由
    app.include_router(hk.router)           # 港股数据路由
    app.include_router(tabular.router)      # 通用表格数据路由
    app.include_router(utility.router)      # 工具类接口路由
    app.include_router(legacy.router)       # 旧版兼容接口路由

    # ------------------------------------------------------------------
    # 注册 WebSocket 端点（实时数据推送）
    # ------------------------------------------------------------------
    from .ws import download_progress, formula as formula_ws, realtime, whole_quote

    app.include_router(realtime.router)           # 实时行情 WebSocket（订阅 xtdata 实时数据）
    app.include_router(whole_quote.router)         # 全推行情 WebSocket
    app.include_router(download_progress.router)   # 数据下载进度 WebSocket
    app.include_router(formula_ws.router)          # 公式计算实时推送 WebSocket

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

        app.include_router(trading.router)   # 普通股票交易路由（下单/撤单/查询）
        app.include_router(credit.router)    # 信用交易（融资融券）路由
        app.include_router(fund.router)      # 资金划转路由
        app.include_router(smt.router)       # 转融通（SMT）交易路由
        app.include_router(bank.router)      # 银证转账路由

        from .ws import trade_callback

        app.include_router(trade_callback.router)  # 交易回调 WebSocket（委托/成交推送）

    return app

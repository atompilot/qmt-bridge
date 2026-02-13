"""后台数据预下载调度模块。

服务启动时立即执行一轮预下载任务，之后每 24 小时定时刷新，确保
基础数据在服务端本地始终可用。

预下载任务清单:
    基础数据（DAILY_TASKS）:
        1. download_sector_data       — 板块成分数据（行业/概念等）
        2. download_holiday_data      — 交易所节假日日历
        3. download_history_contracts — 已到期期货/期权合约列表
        4. download_index_weight      — 指数成分股权重
        5. download_etf_info          — ETF 申购赎回清单
        6. download_cb_data           — 可转债基本信息与转股价格

    增量数据:
        7. K 线增量下载               — 逐只精准增量，绕过 xtquant bug
        8. 财务数据增量下载           — 缓存探测 + 全量补全

这些任务对应 /api/download/* 下的同名端点，客户端通常无需手动调用。
"""

import asyncio
import functools
import logging
from dataclasses import asdict

from xtquant import xtdata

from .config import Settings
from .downloader import (
    DownloadSchedulerState,
    download_financial_incremental,
    download_kline_incremental,
    get_stock_list,
)

logger = logging.getLogger("qmt_bridge")

# (名称, 下载函数) — 每日执行的基础数据下载任务列表
DAILY_TASKS: list[tuple[str, functools.partial]] = [
    ("download_sector_data", functools.partial(xtdata.download_sector_data)),         # 板块成分数据
    ("download_holiday_data", functools.partial(xtdata.download_holiday_data)),        # 节假日日历
    ("download_history_contracts", functools.partial(xtdata.download_history_contracts)),  # 历史合约
    ("download_index_weight", functools.partial(xtdata.download_index_weight)),        # 指数权重
    ("download_etf_info", functools.partial(xtdata.download_etf_info)),               # ETF 信息
    ("download_cb_data", functools.partial(xtdata.download_cb_data)),                 # 可转债数据
]


async def run_daily_downloads() -> None:
    """在线程池中逐个执行 DAILY_TASKS 列表中的下载任务。

    由于 xtdata 的下载接口均为同步阻塞调用，此函数通过
    ``loop.run_in_executor`` 将每个任务放入线程池执行，避免阻塞事件循环。
    任务按顺序依次执行，单个任务失败不会影响后续任务。
    """
    loop = asyncio.get_event_loop()
    for name, func in DAILY_TASKS:
        try:
            await loop.run_in_executor(None, func)
            logger.info("预下载完成: %s", name)
        except Exception:
            logger.exception("预下载失败: %s", name)


async def _run_kline_incremental(
    state: DownloadSchedulerState,
    settings: Settings,
) -> None:
    """在线程池中执行 K 线增量下载（所有配置的周期）。"""
    periods = [p.strip() for p in settings.scheduler_kline_periods.split(",") if p.strip()]
    if not periods:
        return

    loop = asyncio.get_event_loop()

    # 获取股票列表
    try:
        stocks = await loop.run_in_executor(
            None, lambda: get_stock_list(settings.scheduler_kline_sectors),
        )
    except Exception:
        logger.exception("K线增量下载: 获取股票列表失败")
        return

    if not stocks:
        logger.warning("K线增量下载: 股票列表为空，跳过")
        return

    logger.info("K线增量下载开始: 板块=%s, 股票=%d只, 周期=%s",
                settings.scheduler_kline_sectors, len(stocks), periods)

    for period in periods:
        task_key = f"kline:{period}"
        if state.is_running(task_key):
            logger.warning("K线 %s 上一轮未完成，跳过", period)
            continue

        state.set_running(task_key, True)
        try:
            result = await loop.run_in_executor(
                None, lambda p=period: download_kline_incremental(stocks, p),
            )
            state.set_result(task_key, asdict(result))
        except Exception:
            logger.exception("K线增量下载失败: %s", period)
        finally:
            state.set_running(task_key, False)


async def _run_financial_incremental(
    state: DownloadSchedulerState,
    settings: Settings,
) -> None:
    """在线程池中执行财务数据增量下载。"""
    task_key = "financial"
    if state.is_running(task_key):
        logger.warning("财务数据上一轮未完成，跳过")
        return

    loop = asyncio.get_event_loop()

    try:
        stocks = await loop.run_in_executor(
            None, lambda: get_stock_list(settings.scheduler_financial_sectors),
        )
    except Exception:
        logger.exception("财务增量下载: 获取股票列表失败")
        return

    if not stocks:
        logger.warning("财务增量下载: 股票列表为空，跳过")
        return

    logger.info("财务增量下载开始: 板块=%s, 股票=%d只",
                settings.scheduler_financial_sectors, len(stocks))

    state.set_running(task_key, True)
    try:
        result = await loop.run_in_executor(
            None, lambda: download_financial_incremental(stocks),
        )
        state.set_result(task_key, result)
    except Exception:
        logger.exception("财务增量下载失败")
    finally:
        state.set_running(task_key, False)


async def scheduler_loop(
    state: DownloadSchedulerState,
    settings: Settings,
) -> None:
    """预下载调度主循环。

    启动时立即执行一轮全部任务（基础数据 + K 线增量 + 财务增量），
    之后每隔 24 小时重复执行。

    此协程应在应用启动时作为后台任务启动，生命周期与服务进程一致。
    """
    logger.info(
        "定时下载调度器已启动 (K线=%s 周期=%s, 财务=%s)",
        settings.scheduler_kline_enabled,
        settings.scheduler_kline_periods,
        settings.scheduler_financial_enabled,
    )

    while True:
        # 1. 基础数据下载（板块/日历/合约/权重/ETF/转债）
        await run_daily_downloads()

        # 2. K 线增量下载
        if settings.scheduler_kline_enabled:
            try:
                await _run_kline_incremental(state, settings)
            except Exception:
                logger.exception("K线增量下载调度异常")

        # 3. 财务数据增量下载
        if settings.scheduler_financial_enabled:
            try:
                await _run_financial_incremental(state, settings)
            except Exception:
                logger.exception("财务增量下载调度异常")

        # 等待 24 小时后再次执行
        await asyncio.sleep(86400)

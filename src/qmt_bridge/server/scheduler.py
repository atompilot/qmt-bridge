"""后台数据预下载调度模块。

服务启动时立即执行一轮预下载任务，之后每 24 小时定时刷新，确保
基础数据在服务端本地始终可用。

预下载任务清单（对应 DAILY_TASKS）:
    1. download_sector_data       — 板块成分数据（行业/概念等）
    2. download_holiday_data      — 交易所节假日日历
    3. download_history_contracts — 已到期期货/期权合约列表
    4. download_index_weight      — 指数成分股权重
    5. download_etf_info          — ETF 申购赎回清单
    6. download_cb_data           — 可转债基本信息与转股价格

这些任务对应 /api/download/* 下的同名端点，客户端通常无需手动调用。
"""

import asyncio
import functools
import logging

from xtquant import xtdata

logger = logging.getLogger("qmt_bridge")

# (名称, 下载函数) — 每日执行的下载任务列表
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


async def scheduler_loop() -> None:
    """预下载调度主循环。

    启动时立即执行一轮 ``run_daily_downloads()``，确保服务可用时基础数据
    已就绪；之后每隔 24 小时（86400 秒）重复执行，保持数据定期刷新。

    此协程应在应用启动时作为后台任务启动，生命周期与服务进程一致。
    """
    await run_daily_downloads()
    while True:
        await asyncio.sleep(86400)  # 24h
        await run_daily_downloads()

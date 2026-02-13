"""服务端通用下载工具模块。

从 scripts/download_all.py 提取核心下载逻辑，去掉 tqdm/CLI 依赖，改用 logging。
提供：
- download_single_kline()          — 绕过 xtquant bug 的单只 K 线下载
- download_history_data2_safe()    — 替代 xtdata.download_history_data2 的批量入口
- download_kline_incremental()     — K 线增量下载编排（调度器用）
- download_financial_incremental() — 财务增量下载编排（调度器用）
- get_stock_list()                 — 多板块合并去重获取股票列表
- DownloadSchedulerState           — 调度器状态管理（防重叠 + 暴露状态给 API）
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable

import pandas as pd
from xtquant import xtdata

# 直接调用 client.supply_history_data2() 绕过 xtquant 的 download_history_data2 bug:
# 当 result=True（数据已缓存）时，xtquant 的轮询循环永远挂起（回调不触发）。
try:
    from xtquant import xtbson as _BSON_
except ImportError:
    import bson as _BSON_

logger = logging.getLogger("qmt_bridge")

# ── 常量 ──────────────────────────────────────────────────────

# 逐只下载，单只股票的固定超时（秒）。
STOCK_TIMEOUT: dict[str, int] = {
    "1m": 10, "5m": 10, "15m": 10, "30m": 5, "60m": 5, "1d": 5,
}

# 财务数据 future 轮询间隔（秒）
POLL_INTERVAL = 0.5

# 缓存探测每批股票数
PROBE_BATCH_SIZE = 200

# 增量下载安全重叠天数
SAFETY_OVERLAP_DAYS = 1

# K 线历史完整性检查年数
KLINE_HISTORY_CHECK_YEARS = 3

# 财务数据过期天数（季报周期约 90 天）
FINANCIAL_STALE_DAYS = 90

# 财务数据最少记录数（低于此值视为数据不完整）
FINANCIAL_MIN_RECORDS = 8

# 默认板块
DEFAULT_SECTORS = "沪深A股,沪深ETF,沪深指数"


# ── 结果数据类 ────────────────────────────────────────────────

@dataclass
class KlineDownloadResult:
    """单次 K 线下载的统计结果。"""
    ok: int = 0
    fail: int = 0
    timeout: int = 0
    failed_indices: list[int] = field(default_factory=list)


@dataclass
class IncrementalResult:
    """增量下载编排的统计结果。"""
    period: str = ""
    ok: int = 0
    fail: int = 0
    timeout: int = 0
    date_groups: int = 0
    elapsed: float = 0.0


# ── 调度器状态管理 ────────────────────────────────────────────

class DownloadSchedulerState:
    """防止任务重叠 + 暴露状态给 API。"""

    def __init__(self) -> None:
        self._running: dict[str, bool] = {}
        self._last_results: dict[str, dict] = {}
        self._last_run_times: dict[str, datetime] = {}

    def is_running(self, task_key: str) -> bool:
        return self._running.get(task_key, False)

    def set_running(self, task_key: str, running: bool) -> None:
        self._running[task_key] = running

    def set_result(self, task_key: str, result: dict) -> None:
        self._last_results[task_key] = result
        self._last_run_times[task_key] = datetime.now()

    def status(self) -> dict:
        """返回调度器状态字典，供 API 端点查询。"""
        return {
            "running": dict(self._running),
            "last_results": dict(self._last_results),
            "last_run_times": {
                k: v.isoformat(timespec="seconds")
                for k, v in self._last_run_times.items()
            },
        }


# ── 工具函数 ──────────────────────────────────────────────────

def make_batches(lst: list, size: int) -> list[list]:
    """将列表按 size 切分为子列表。"""
    return [lst[i : i + size] for i in range(0, len(lst), size)]


def wait_future(future, timeout: float) -> None:
    """等待 future 完成，每 POLL_INTERVAL 秒醒来让 Python 有机会处理中断。

    在 Windows 上 future.result(timeout=N) 会长时间阻塞主线程，
    这里用短轮询替代。
    """
    deadline = time.monotonic() + timeout
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise FutureTimeoutError()
        try:
            future.result(timeout=min(remaining, POLL_INTERVAL))
            return
        except FutureTimeoutError:
            if time.monotonic() >= deadline:
                raise


def get_stock_list(sectors: str = DEFAULT_SECTORS) -> list[str]:
    """多板块合并去重获取股票列表。

    Args:
        sectors: 逗号分隔的板块名称字符串。

    Returns:
        去重后的股票代码列表（保持首次出现顺序）。
    """
    sector_list = [s.strip() for s in sectors.split(",")]
    stocks: list[str] = []
    seen: set[str] = set()
    for sector in sector_list:
        codes = xtdata.get_stock_list_in_sector(sector)
        logger.info("板块 [%s] 返回 %d 只", sector, len(codes))
        for c in codes:
            if c not in seen:
                seen.add(c)
                stocks.append(c)
    return stocks


# ── 核心下载函数 ──────────────────────────────────────────────

def download_single_kline(
    client,
    code: str,
    period: str,
    start_time: str = "",
    end_time: str = "",
    incrementally: bool | None = None,
    timeout: float | None = None,
) -> str:
    """直接调用 client.supply_history_data2() 下载单只股票 K 线。

    绕过 xtquant.download_history_data2 的 bug：
    当 result=True（数据已缓存）时，xtquant 的轮询循环会永远挂起，
    因为回调永远不会被触发。

    Args:
        client: xtdata.get_client() 返回的 C++ 客户端对象。
        code: 股票代码，如 "000001.SZ"。
        period: K 线周期，如 "1d"/"1m"/"5m"。
        start_time: 开始时间，格式 "YYYYMMDD"。
        end_time: 结束时间，格式同上。
        incrementally: True=增量, False=全量, None=自动。
        timeout: 超时秒数，None 时根据 period 自动选择。

    Returns:
        "ok" | "timeout" | "error: ..." | "disconnected"
    """
    if timeout is None:
        timeout = STOCK_TIMEOUT.get(period, 10)
    if incrementally is None:
        incrementally = not bool(start_time)
    param = {"incrementally": incrementally}
    bson_param = _BSON_.BSON.encode(param)

    status = {"done": False, "error": ""}

    def on_progress(data):
        total_val = data.get("total", 0)
        if total_val < 0:
            status["error"] = data.get("message", "unknown error")
            status["done"] = True
            return True
        finished = data.get("finished", 0)
        if finished >= total_val and total_val > 0:
            status["done"] = True
        return status["done"]

    result = client.supply_history_data2(
        [code], period, start_time, end_time, bson_param, on_progress,
    )

    if result:
        # result=True: 异步下载已提交，但回调不会触发。
        # 轮询本地数据确认目标时间范围内已有数据。
        # 先立即检查一次（无 sleep），多数情况下数据已在本地，0 开销通过。
        deadline = time.monotonic() + timeout
        while True:
            if not client.is_connected():
                return "disconnected"
            try:
                check = xtdata.get_local_data(
                    field_list=[], stock_list=[code],
                    period=period,
                    start_time=start_time, end_time=end_time,
                    count=1,
                )
                if code in check and check[code] is not None and not check[code].empty:
                    return "ok"
            except Exception:
                pass
            if time.monotonic() >= deadline:
                return "timeout"
            time.sleep(0.1)

    deadline = time.monotonic() + timeout
    while not status["done"]:
        if not client.is_connected():
            return "disconnected"
        if time.monotonic() >= deadline:
            return "timeout"
        time.sleep(0.1)

    if status["error"]:
        return f"error: {status['error']}"
    return "ok"


# ── 批量下载 (替代 xtdata.download_history_data2) ────────────

def download_history_data2_safe(
    stock_list: list[str],
    period: str = "1d",
    start_time: str = "",
    end_time: str = "",
    callback: Callable[[dict], None] | None = None,
) -> dict[str, str]:
    """替代 xtdata.download_history_data2，逐只调用 download_single_kline。

    Args:
        stock_list: 股票代码列表。
        period: K 线周期。
        start_time: 开始时间。
        end_time: 结束时间。
        callback: 进度回调，格式 {"finished": i, "total": n, "stock": code, "status": status}。

    Returns:
        {stock_code: status_string}
    """
    client = xtdata.get_client()
    total = len(stock_list)
    results: dict[str, str] = {}
    timeout = STOCK_TIMEOUT.get(period, 10)

    for i, code in enumerate(stock_list):
        try:
            status = download_single_kline(
                client, code, period, start_time, end_time, timeout=timeout,
            )
        except Exception as exc:
            status = f"error: {exc}"
            logger.error("K线下载异常 %s %s: %s", period, code, exc)

        results[code] = status
        if status != "ok":
            logger.warning("K线下载 %s %s: %s", period, code, status)

        if callback is not None:
            callback({
                "finished": i + 1,
                "total": total,
                "stock": code,
                "status": status,
            })

    return results


# ── 缓存探测 ─────────────────────────────────────────────────

def probe_local_dates(stocks: list[str], period: str) -> dict[str, str]:
    """批量探测每只股票本地缓存的最新数据日期。

    Returns:
        {stock_code: "YYYYMMDD"} — 无本地数据的股票不在字典中。
    """
    result: dict[str, str] = {}
    for i in range(0, len(stocks), PROBE_BATCH_SIZE):
        batch = stocks[i : i + PROBE_BATCH_SIZE]
        try:
            data = xtdata.get_local_data(
                field_list=[], stock_list=batch,
                period=period, start_time="", end_time="", count=1,
            )
            for stock, df in data.items():
                if df is not None and not df.empty:
                    last_ts = df.index[-1]
                    if isinstance(last_ts, (int, float)):
                        dt = datetime.fromtimestamp(last_ts / 1000)
                    else:
                        dt = pd.Timestamp(last_ts).to_pydatetime()
                    result[stock] = dt.strftime("%Y%m%d")
        except Exception as exc:
            logger.warning("缓存探测批次失败: %s", exc)
    return result


def probe_financial_cache(
    stocks: list[str], table_list: list[str],
) -> tuple[set[str], int, int]:
    """探测哪些股票已有完整且新鲜的本地财务数据缓存。

    Returns:
        (新鲜完整的股票代码集合, 过期股票数量, 数据不完整的股票数量)
    """
    fresh: set[str] = set()
    stale_count = 0
    incomplete_count = 0
    check_table = table_list[0]
    stale_cutoff = (datetime.now() - timedelta(days=FINANCIAL_STALE_DAYS)).strftime("%Y%m%d")

    for batch in make_batches(stocks, PROBE_BATCH_SIZE):
        try:
            data = xtdata.get_financial_data(batch, [check_table])
            for stock, tables_data in data.items():
                if not isinstance(tables_data, dict):
                    continue
                df = tables_data.get(check_table)
                if df is None or not isinstance(df, pd.DataFrame) or df.empty:
                    continue
                if len(df) < FINANCIAL_MIN_RECORDS:
                    incomplete_count += 1
                    continue
                if "m_anntime" in df.columns:
                    max_ann = df["m_anntime"].dropna()
                    if not max_ann.empty:
                        latest = str(max_ann.max())
                        if latest >= stale_cutoff:
                            fresh.add(stock)
                        else:
                            stale_count += 1
                    else:
                        stale_count += 1
                else:
                    fresh.add(stock)
        except Exception as exc:
            logger.warning("财务缓存探测批次失败: %s", exc)
    return fresh, stale_count, incomplete_count


def group_stocks_by_date(
    stocks: list[str],
    local_dates: dict[str, str],
) -> list[tuple[str, list[str]]]:
    """按本地缓存最新日期分组。

    Returns:
        [(start_time, [stock_codes]), ...] 按 start_time 排序（""在最前）。
    """
    groups: dict[str, list[str]] = defaultdict(list)
    for stock in stocks:
        last_date = local_dates.get(stock)
        if last_date:
            overlap_dt = datetime.strptime(last_date, "%Y%m%d") - timedelta(days=SAFETY_OVERLAP_DAYS)
            groups[overlap_dt.strftime("%Y%m%d")].append(stock)
        else:
            groups[""].append(stock)
    return sorted(groups.items(), key=lambda x: x[0])


# ── K 线批量下载（无 tqdm） ──────────────────────────────────

def _run_kline_downloads(
    client,
    stocks: list[str],
    stock_indices: list[int],
    period: str,
    start_time: str,
    end_time: str,
    incrementally: bool | None,
    timeout: int,
) -> KlineDownloadResult:
    """逐只下载 K 线数据（直接调用 client.supply_history_data2）。"""
    res = KlineDownloadResult()
    for idx in stock_indices:
        code = stocks[idx]
        try:
            status = download_single_kline(
                client, code, period, start_time, end_time,
                incrementally, timeout,
            )
            if status == "ok":
                res.ok += 1
                logger.debug("K线 %s %s %s", period, code, status)
            elif status == "timeout":
                res.timeout += 1
                res.fail += 1
                res.failed_indices.append(idx)
                logger.error("K线 %s %s 超时 (%d秒)", period, code, timeout)
            elif status == "disconnected":
                res.fail += 1
                res.failed_indices.append(idx)
                logger.error("K线 %s %s 连接断开", period, code)
            else:
                res.fail += 1
                res.failed_indices.append(idx)
                logger.error("K线 %s %s %s", period, code, status)
        except Exception as exc:
            res.fail += 1
            res.failed_indices.append(idx)
            logger.error("K线 %s %s 异常: %s", period, code, exc)
    return res


# ── 增量下载编排（调度器用） ──────────────────────────────────

def download_kline_incremental(
    stocks: list[str],
    period: str,
    max_retries: int = 2,
) -> IncrementalResult:
    """精准增量下载一个周期的 K 线数据（Mode C）。

    基于本地缓存探测，每只股票从各自的最新缓存日期开始增量下载。
    """
    t0 = time.time()
    client = xtdata.get_client()
    effective_timeout = STOCK_TIMEOUT.get(period, 10)
    incrementally = True

    logger.info("K线增量下载开始: %s, 股票 %d 只", period, len(stocks))

    # 缓存探测
    local_dates = probe_local_dates(stocks, period)
    today_str = datetime.now().strftime("%Y%m%d")

    # 历史完整性检查
    incomplete_stocks: set[str] = set()
    stocks_with_cache = [s for s in stocks if s in local_dates]
    if stocks_with_cache:
        sentinel_year = datetime.now().year - KLINE_HISTORY_CHECK_YEARS
        has_history: set[str] = set()
        for batch in make_batches(stocks_with_cache, PROBE_BATCH_SIZE):
            try:
                data = xtdata.get_local_data(
                    field_list=[], stock_list=batch, period=period,
                    start_time=f"{sentinel_year}0101",
                    end_time=f"{sentinel_year}1231", count=1,
                )
                for stock, df in data.items():
                    if df is not None and not df.empty:
                        has_history.add(stock)
            except Exception as exc:
                logger.warning("历史完整性探测失败: %s", exc)
        incomplete_stocks = set(stocks_with_cache) - has_history

    # 按缺口排序并构建逐只日期组
    def _gap_sort_key(s: str) -> int:
        if s not in local_dates:
            return 999999
        if s in incomplete_stocks:
            return 999998
        d = local_dates[s]
        return (datetime.strptime(today_str, "%Y%m%d") - datetime.strptime(d, "%Y%m%d")).days

    sorted_stocks = sorted(stocks, key=_gap_sort_key, reverse=True)
    date_groups: list[tuple[str, str, list[str]]] = []
    for s in sorted_stocks:
        d = local_dates.get(s)
        if d and s not in incomplete_stocks:
            overlap_dt = datetime.strptime(d, "%Y%m%d") - timedelta(days=SAFETY_OVERLAP_DAYS)
            st = overlap_dt.strftime("%Y%m%d")
        else:
            st = ""
        date_groups.append((st, "", [s]))

    n_no_cache = sum(1 for s in sorted_stocks if s not in local_dates)
    n_incomplete = len(incomplete_stocks)
    n_ok = len(sorted_stocks) - n_no_cache - n_incomplete
    logger.info(
        "K线 %s 缓存探测: 无缓存 %d, 历史不完整 %d, 正常增量 %d",
        period, n_no_cache, n_incomplete, n_ok,
    )

    # 按组逐只下载
    total_ok = 0
    total_fail = 0
    total_to = 0

    for start_time, end_time, group_stocks in date_groups:
        all_indices = list(range(len(group_stocks)))
        res = _run_kline_downloads(
            client, group_stocks, all_indices, period, start_time, end_time,
            incrementally, effective_timeout,
        )

        # 自动重试
        failed = res.failed_indices
        ok = res.ok
        for retry_round in range(1, max_retries + 1):
            if not failed:
                break
            retry_timeout = int(effective_timeout * (1.5 ** retry_round))
            logger.info("K线 %s 重试第 %d 轮: %d 只, 超时 %ds", period, retry_round, len(failed), retry_timeout)
            r = _run_kline_downloads(
                client, group_stocks, failed, period, start_time, end_time,
                incrementally, retry_timeout,
            )
            ok += r.ok
            failed = r.failed_indices

        final_fail = len(failed)
        ok = len(group_stocks) - final_fail
        total_ok += ok
        total_fail += final_fail
        total_to += len(failed)

    elapsed = time.time() - t0
    logger.info(
        "K线 %s 增量下载完成: 成功 %d, 失败 %d, 耗时 %.1f秒, 日期组 %d",
        period, total_ok, total_fail, elapsed, len(date_groups),
    )
    return IncrementalResult(
        period=period, ok=total_ok, fail=total_fail,
        timeout=total_to, date_groups=len(date_groups), elapsed=elapsed,
    )


def download_financial_incremental(
    stocks: list[str],
    table_list: list[str] | None = None,
    batch_size: int = 20,
    timeout: int = 120,
    delay: float = 0.2,
    max_retries: int = 2,
) -> dict[str, int]:
    """财务数据增量下载编排（调度器用）。

    先探测缓存，跳过已有完整新鲜数据的股票，只下载需要更新的部分。

    Returns:
        {"ok": n, "fail": n, "timeout": n}
    """
    if table_list is None:
        table_list = ["Balance", "Income", "CashFlow"]

    n_original = len(stocks)
    logger.info("财务增量下载开始: %d 只股票", n_original)

    # 缓存探测
    fresh, n_stale, n_incomplete = probe_financial_cache(stocks, table_list)
    need_download = [s for s in stocks if s not in fresh]
    n_fresh = len(fresh)
    n_no_data = len(need_download) - n_stale - n_incomplete
    logger.info(
        "财务缓存探测: 新鲜 %d, 过期 %d, 不完整 %d, 无缓存 %d",
        n_fresh, n_stale, n_incomplete, n_no_data,
    )

    if not need_download:
        logger.info("财务数据全部缓存有效，跳过下载")
        return {"ok": n_original, "fail": 0, "timeout": 0}

    stocks = need_download
    batches = make_batches(stocks, batch_size)
    all_indices = list(range(len(batches)))

    logger.info("开始下载财务数据: %d 批 (%d 只)", len(batches), len(stocks))

    # 首轮下载
    ok, fail, to, failed = _run_financial_batches(batches, all_indices, table_list, timeout, delay)

    # 自动重试
    for retry_round in range(1, max_retries + 1):
        if not failed:
            break
        retry_timeout = int(timeout * (1.5 ** retry_round))
        retry_stocks = sum(len(batches[i]) for i in failed)
        logger.info(
            "财务数据重试第 %d 轮: %d 批 (%d 只), 超时 %ds",
            retry_round, len(failed), retry_stocks, retry_timeout,
        )
        r_ok, r_fail, r_to, still_failed = _run_financial_batches(
            batches, failed, table_list, retry_timeout, delay,
        )
        ok += r_ok
        failed = still_failed

    n_cached = n_original - len(stocks)
    final_fail_stocks = sum(len(batches[i]) for i in failed)
    ok = len(stocks) - final_fail_stocks + n_cached
    fail = final_fail_stocks
    to = len(failed)

    logger.info("财务数据完成: 成功 %d (缓存 %d), 失败 %d (超时 %d)", ok, n_cached, fail, to)
    return {"ok": ok, "fail": fail, "timeout": to}


def _run_financial_batches(
    batches: list[list[str]],
    batch_indices: list[int],
    table_list: list[str],
    timeout: int,
    delay: float,
) -> tuple[int, int, int, list[int]]:
    """执行一轮财务数据批次下载。

    Returns:
        (ok_count, fail_count, timeout_count, failed_indices)
    """
    ok_count = 0
    fail_count = 0
    timeout_count = 0
    failed_indices: list[int] = []
    n_total = len(batch_indices)

    for seq, idx in enumerate(batch_indices):
        batch = batches[idx]
        cancelled = [False]

        executor = ThreadPoolExecutor(max_workers=1)
        try:
            future = executor.submit(
                xtdata.download_financial_data2,
                stock_list=batch,
                table_list=table_list,
            )
            wait_future(future, timeout)
            ok_count += len(batch)
            logger.debug("财务数据批次 %d 成功 (%d 只)", idx + 1, len(batch))
        except FutureTimeoutError:
            cancelled[0] = True
            timeout_count += 1
            fail_count += len(batch)
            failed_indices.append(idx)
            logger.error("财务数据批次 %d 超时 (%d秒, %d 只)", idx + 1, timeout, len(batch))
        except Exception as exc:
            cancelled[0] = True
            fail_count += len(batch)
            failed_indices.append(idx)
            logger.error("财务数据批次 %d 失败 (%d 只): %s", idx + 1, len(batch), exc)
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

        if delay > 0 and seq < n_total - 1:
            time.sleep(delay)

    return ok_count, fail_count, timeout_count, failed_indices

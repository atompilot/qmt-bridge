"""逐股精准增量下载沪深 A 股历史 K 线 + 财务数据。

基于本地缓存探测，每只股票从各自的最新缓存日期开始增量下载。
首次运行自动全量，后续运行自动精准增量。

支持 --since YYYY 按年度分段下载，适合快速获取近期数据后逐步回填历史。

用法:
    python scripts/download_all.py [OPTIONS]
    python scripts/download_all.py --periods 1m --skip-financial --since 2025
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from xtquant import xtdata

# 直接调用 client.supply_history_data2() 绕过 xtquant 的 download_history_data2 bug:
# 当 result=True（数据已缓存）时，xtquant 的轮询循环永远挂起（回调不触发）。
try:
    from xtquant import xtbson as _BSON_
except ImportError:
    import bson as _BSON_

# 财务数据仍用 ThreadPoolExecutor，future.result(timeout=N) 在 Windows 上
# 会长时间阻塞主线程导致 Ctrl+C 无响应，改用短轮询让 Python 有机会处理中断。
POLL_INTERVAL = 0.5

try:
    from tqdm import tqdm
except ImportError:
    print("错误: 需要 tqdm 依赖，请先执行: pip install tqdm>=4.60")
    print("  或: pip install -e \".[scripts]\"")
    sys.exit(1)

# 逐只下载，单只股票的固定超时（秒）。
# 正常 <1 秒完成，卡死的等再久也不会好，快速跳过。
STOCK_TIMEOUT: dict[str, int] = {
    "1m": 10,
    "5m": 10,
    "15m": 10,
    "30m": 5,
    "60m": 5,
    "1d": 5,
}

# ── 默认下载板块 ─────────────────────────────────────────────
# xtdata.get_sector_list() 返回的市场板块（共 30 个，不含 SW/CSRC 行业分类）:
#
# 股票:
#   沪深A股 (5189)    = 上证A股 (2306) + 深证A股 (2883)，含创业板 (1392) 和科创板 (602)
#   沪深京A股 (5501)  = 沪深A股 + 京市A股 (312)
#   沪深B股 (79)      = 上证B股 (41) + 深证B股 (38)
#   科创板CDR (1)
#
# ETF:
#   沪深ETF (1460)    = 沪市ETF (855) + 深市ETF (605)
#
# 指数:
#   沪深指数 (609)    = 沪市指数 (221) + 深市指数 (388)
#
# 转债:
#   沪深转债 (383)    = 上证转债 (187) + 深证转债 (196)
#
# 债券:
#   沪深债券 (39583)  = 沪市债券 (21268) + 深市债券 (18315)
#
# 基金:
#   沪深基金 (2004)   = 沪市基金 (1027) + 深市基金 (977)
#
# 期权:
#   上证期权 (760), 深证期权 (616)
#
# 港股:
#   香港联交所股票 (882), 香港联交所指数 (0)
#
DEFAULT_SECTORS = "沪深A股,沪深ETF,沪深指数"

# ── 常量 ──────────────────────────────────────────────────────
PROBE_BATCH_SIZE = 200
SAFETY_OVERLAP_DAYS = 1

# Ctrl+C 中断标记：xtdata 下载线程是非 daemon 线程，
# 即使 executor.shutdown(wait=False) 也无法终止已运行的线程，
# Python 退出时会等待这些线程完成导致卡死。
# 设置此标记后 main() 结束时用 os._exit(0) 强制退出。
_interrupted = False

# ── 日志配置 ──────────────────────────────────────────────────

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logger = logging.getLogger("download_all")
logger.setLevel(logging.DEBUG)

# 文件 handler：详细日志写入 logs/download_all_<date>.log
_log_file = LOG_DIR / f"download_all_{datetime.now():%Y%m%d_%H%M%S}.log"
_fh = logging.FileHandler(_log_file, encoding="utf-8")
_fh.setLevel(logging.DEBUG)
_fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)-7s %(message)s"))
logger.addHandler(_fh)

# 控制台 handler：仅 WARNING 以上（避免与 tqdm 冲突）
_ch = logging.StreamHandler()
_ch.setLevel(logging.WARNING)
_ch.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
logger.addHandler(_ch)

# ── 状态持久化 ────────────────────────────────────────────────

STATE_FILE = LOG_DIR / "download_state.json"
STATE_VERSION = 1


@dataclass
class TaskState:
    """单个下载任务的状态。"""
    last_success_date: str = ""
    last_run_iso: str = ""
    stock_count: int = 0
    ok: int = 0
    fail: int = 0


@dataclass
class DownloadState:
    """全局下载状态容器。"""
    version: int = STATE_VERSION
    tasks: dict[str, TaskState] = field(default_factory=dict)


def load_state() -> DownloadState:
    """读取状态文件，异常时回退空状态。"""
    if not STATE_FILE.exists():
        return DownloadState()
    try:
        raw = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        state = DownloadState(version=raw.get("version", STATE_VERSION))
        for key, val in raw.get("tasks", {}).items():
            state.tasks[key] = TaskState(**val)
        return state
    except Exception as exc:
        logger.warning("读取状态文件失败，使用空状态: %s", exc)
        return DownloadState()


def save_state(state: DownloadState) -> None:
    """将状态写入 JSON 文件。"""
    data = {
        "version": state.version,
        "tasks": {k: asdict(v) for k, v in state.tasks.items()},
    }
    STATE_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("状态已保存: %s", STATE_FILE)


# ── 工具函数 ──────────────────────────────────────────────────

def make_batches(lst: list, size: int) -> list[list]:
    """将列表按 size 切分为子列表。"""
    return [lst[i : i + size] for i in range(0, len(lst), size)]


def _download_single_kline(
    client,
    code: str,
    period: str,
    start_time: str,
    end_time: str,
    incrementally: bool | None,
    timeout: float,
) -> str:
    """直接调用 client.supply_history_data2() 下载单只股票 K 线。

    绕过 xtquant.download_history_data2 的 bug：
    当 result=True（数据已缓存）时，xtquant 的轮询循环会永远挂起，
    因为回调永远不会被触发。

    Args:
        incrementally: True=增量, False=全量, None=自动(start_time 非空→False, 空→True)。

    Returns:
        "ok" | "timeout" | "cached" | "error: ..." | "disconnected"
    """
    # 解析 incrementally: None → 根据 start_time 自动决定
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
        # result=True: 数据已缓存，C++ 同步返回，回调不会触发。
        # 这就是 xtquant download_history_data2 的 bug 所在:
        # 它在此情况下仍然无限轮询等待回调，导致永远挂起。
        return "cached"

    # result=False: 异步下载，轮询等待完成
    deadline = time.monotonic() + timeout
    while not status["done"]:
        if not client.is_connected():
            return "disconnected"
        if time.monotonic() >= deadline:
            return "timeout"
        time.sleep(0.1)  # 0.1s 轮询，KeyboardInterrupt 可在此处被捕获

    if status["error"]:
        return f"error: {status['error']}"
    return "ok"


def _wait_future(future, timeout: float) -> None:
    """等待 future 完成，每 POLL_INTERVAL 秒醒来检查 KeyboardInterrupt。

    在 Windows 上 future.result(timeout=N) 会长时间阻塞主线程，
    Ctrl+C 信号要等到 timeout 到期才能被处理。
    这里用短轮询替代，确保 Ctrl+C 能在 0.5 秒内响应。
    """
    deadline = time.monotonic() + timeout
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise FutureTimeoutError()
        try:
            future.result(timeout=min(remaining, POLL_INTERVAL))
            return  # 成功完成
        except FutureTimeoutError:
            if time.monotonic() >= deadline:
                raise
            # 未超时，继续轮询（此处 KeyboardInterrupt 可被捕获）


def _run_kline_downloads(
    client,
    stocks: list[str],
    stock_indices: list[int],
    period: str,
    start_time: str,
    end_time: str,
    incrementally: bool | None,
    timeout: int,
    pbar: tqdm,
    label: str,
) -> tuple[int, int, int, list[int], bool]:
    """逐只下载 K 线数据（直接调用 client.supply_history_data2）。

    Args:
        client: xtdata.get_client() 返回的 C++ 客户端对象。
        incrementally: True=增量, False=全量, None=自动决定。

    Returns:
        (ok_count, fail_count, timeout_count, failed_indices, interrupted)
    """
    ok_count = 0
    fail_count = 0
    timeout_count = 0
    failed_indices: list[int] = []
    n_total = len(stock_indices)

    for seq, idx in enumerate(stock_indices):
        code = stocks[idx]
        pbar.set_description(f"{label} [{seq+1}/{n_total}]")
        parts = [code]
        if fail_count or timeout_count:
            parts.append(f"失败:{fail_count} 超时:{timeout_count}")
        pbar.set_postfix_str(" | ".join(parts), refresh=True)

        try:
            result = _download_single_kline(
                client, code, period, start_time, end_time,
                incrementally, timeout,
            )
            if result in ("ok", "cached"):
                ok_count += 1
                logger.debug("K线 %s %s %s", period, code, result)
            elif result == "timeout":
                timeout_count += 1
                fail_count += 1
                failed_indices.append(idx)
                logger.error("K线 %s %s 超时 (%d秒)", period, code, timeout)
                tqdm.write(f"  ⚠ {code} 超时 ({timeout}s)")
            elif result == "disconnected":
                fail_count += 1
                failed_indices.append(idx)
                logger.error("K线 %s %s 连接断开", period, code)
                tqdm.write(f"  ⚠ {code} 连接断开")
            else:
                # "error: ..." 消息
                fail_count += 1
                failed_indices.append(idx)
                logger.error("K线 %s %s %s", period, code, result)
                tqdm.write(f"  ⚠ {code} {result}")
        except KeyboardInterrupt:
            global _interrupted
            _interrupted = True
            logger.warning("K线 %s 被用户中断", period)
            tqdm.write(f"\n  用户中断，K线 {period} 本轮已完成 {ok_count} 只")
            return ok_count, fail_count, timeout_count, failed_indices, True
        except Exception as exc:
            fail_count += 1
            failed_indices.append(idx)
            logger.error("K线 %s %s 异常: %s", period, code, exc)
            tqdm.write(f"  ⚠ {code} 异常: {exc}")
        finally:
            pbar.update(1)

    return ok_count, fail_count, timeout_count, failed_indices, False


def _make_financial_cb(
    flag: list[bool], codes: list[str], tables: list[str],
    fail_count: int, timeout_count: int, pbar: tqdm,
) -> callable:
    """创建财务数据下载回调，用于更新 tqdm 进度条。"""
    n_codes = len(codes)
    n_tables = len(tables)
    def _on_progress(data: dict) -> None:
        if flag[0]:
            return
        finished = data.get("finished", 0)
        total = data.get("total", 0)
        parts = [f"批内 {finished}/{total}"]
        if total > 0:
            item_est = min(int(finished * n_codes * n_tables / total), n_codes * n_tables) - 1
            if item_est >= 0:
                stock_idx = item_est // n_tables
                table_idx = item_est % n_tables
                if stock_idx < n_codes:
                    parts.append(f"{codes[stock_idx]}/{tables[table_idx]}")
        if fail_count or timeout_count:
            parts.append(f"失败:{fail_count} 超时:{timeout_count}")
        pbar.set_postfix_str(" | ".join(parts), refresh=True)
    return _on_progress


def _run_financial_batches(
    batches: list[list[str]],
    batch_indices: list[int],
    table_list: list[str],
    timeout: int,
    delay: float,
    pbar: tqdm,
    label: str,
) -> tuple[int, int, int, list[int], bool]:
    """执行一轮财务数据批次下载。

    Returns:
        (ok_count, fail_count, timeout_count, failed_indices, interrupted)
    """
    ok_count = 0
    fail_count = 0
    timeout_count = 0
    failed_indices: list[int] = []
    n_total = len(batch_indices)

    for seq, idx in enumerate(batch_indices):
        batch = batches[idx]
        batch_items = len(batch) * len(table_list)
        cancelled = [False]
        pbar.set_description(f"{label} [{seq+1}/{n_total}批]")

        executor = ThreadPoolExecutor(max_workers=1)
        try:
            future = executor.submit(
                xtdata.download_financial_data2,
                stock_list=batch,
                table_list=table_list,
                callback=_make_financial_cb(cancelled, batch, table_list, fail_count, timeout_count, pbar),
            )
            _wait_future(future, timeout)
            ok_count += len(batch)
            logger.debug("财务数据批次 %d 成功 (%d 只)", idx+1, len(batch))
        except FutureTimeoutError:
            cancelled[0] = True
            timeout_count += 1
            fail_count += len(batch)
            failed_indices.append(idx)
            logger.error("财务数据批次 %d 超时 (%d秒, %d 只)", idx+1, timeout, len(batch))
            tqdm.write(f"  ⚠ 批次 {idx+1} 超时 ({timeout}s, {len(batch)} 只)")
        except KeyboardInterrupt:
            global _interrupted  # noqa: PLW0602 (already declared in kline handler)
            _interrupted = True
            cancelled[0] = True
            executor.shutdown(wait=False, cancel_futures=True)
            pbar.close()
            logger.warning("财务数据被用户中断")
            tqdm.write(f"\n  用户中断，财务数据本轮已完成 {ok_count} 只")
            return ok_count, fail_count, timeout_count, failed_indices, True
        except Exception as exc:
            cancelled[0] = True
            fail_count += len(batch)
            failed_indices.append(idx)
            logger.error("财务数据批次 %d 失败 (%d 只): %s", idx+1, len(batch), exc)
            tqdm.write(f"  ⚠ 批次 {idx+1} 失败 ({len(batch)} 只): {exc}")
        finally:
            executor.shutdown(wait=False, cancel_futures=True)
            pbar.update(batch_items)

        if delay > 0 and seq < n_total - 1:
            time.sleep(delay)
    else:
        pbar.close()

    return ok_count, fail_count, timeout_count, failed_indices, False


# 财务数据的公告日期距今超过此天数，认为数据可能过期，需重新下载。
# 中国上市公司季报披露周期: Q1(4/30前), H1(8/31前), Q3(10/31前), 年报(4/30前)。
# 90 天基本覆盖一个季度间隔。
FINANCIAL_STALE_DAYS = 90


def probe_financial_cache(
    stocks: list[str], table_list: list[str],
) -> tuple[set[str], int]:
    """探测哪些股票已有新鲜的本地财务数据缓存。

    只检查第一个报表的最新公告日期(m_anntime)：
    - 距今 ≤ FINANCIAL_STALE_DAYS → 新鲜，跳过
    - 距今 > FINANCIAL_STALE_DAYS → 过期，需重新下载

    Returns:
        (新鲜的股票代码集合, 过期股票数量)
    """
    fresh: set[str] = set()
    stale_count = 0
    check_table = table_list[0]
    stale_cutoff = (datetime.now() - timedelta(days=FINANCIAL_STALE_DAYS)).strftime("%Y%m%d")

    probe_pbar = tqdm(total=len(stocks), desc="探测财务缓存", unit="只")
    for batch in make_batches(stocks, PROBE_BATCH_SIZE):
        try:
            data = xtdata.get_financial_data(batch, [check_table])
            for stock, tables_data in data.items():
                if not isinstance(tables_data, dict):
                    continue
                df = tables_data.get(check_table)
                if df is None or not isinstance(df, pd.DataFrame) or df.empty:
                    continue
                # 检查最新公告日期
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
                    # 无法判断日期，保守认为新鲜
                    fresh.add(stock)
        except Exception as exc:
            logger.warning("财务缓存探测批次失败: %s", exc)
        probe_pbar.update(len(batch))
    probe_pbar.close()
    return fresh, stale_count


def download_financial(
    stocks: list[str],
    table_list: list[str],
    batch_size: int,
    timeout: int = 120,
    delay: float = 0.2,
    max_retries: int = 2,
    full: bool = False,
) -> dict[str, int]:
    """下载财务数据，返回 {"ok": n, "fail": n, "timeout": n}。

    通过 callback 实现逐项（股票 × 报表）粒度的进度更新。
    每批下载有超时保护，批次间有延迟以缓解服务端压力。
    超时失败的批次会自动重试，每轮重试超时再增加 50%。

    full=False 时先探测缓存，跳过已有数据的股票。
    """
    # ── 缓存探测 ──
    n_original = len(stocks)
    if not full:
        tqdm.write("探测财务数据本地缓存...")
        fresh, n_stale = probe_financial_cache(stocks, table_list)
        need_download = [s for s in stocks if s not in fresh]
        n_fresh = len(fresh)
        n_no_data = len(need_download) - n_stale
        if n_fresh:
            tqdm.write(f"  · {n_fresh} 只缓存新鲜 (≤{FINANCIAL_STALE_DAYS}天)，跳过")
        if n_stale:
            tqdm.write(f"  · {n_stale} 只缓存过期 (>{FINANCIAL_STALE_DAYS}天)，重新下载")
        if n_no_data:
            tqdm.write(f"  · {n_no_data} 只无缓存，全新下载")
        logger.info(
            "财务缓存探测: 新鲜 %d, 过期 %d, 无缓存 %d",
            n_fresh, n_stale, n_no_data,
        )
        if not need_download:
            tqdm.write("  · 全部已有缓存，跳过财务数据下载")
            return {"ok": n_original, "fail": 0, "timeout": 0}
        stocks = need_download

    batches = make_batches(stocks, batch_size)
    total_items = len(stocks) * len(table_list)
    n_batches = len(batches)
    all_indices = list(range(n_batches))

    logger.info(
        "开始下载财务数据，共 %d 批 (%d 只 × %d 表 = %d 项)",
        n_batches, len(stocks), len(table_list), total_items,
    )
    pbar = tqdm(total=total_items, desc="财务", unit="项")

    # ── 首轮下载 ──
    ok, fail, to, failed, interrupted = _run_financial_batches(
        batches, all_indices, table_list, timeout, delay, pbar, "财务",
    )

    # ── 自动重试失败批次 ──
    for retry_round in range(1, max_retries + 1):
        if not failed or interrupted:
            break
        retry_timeout = int(timeout * (1.5 ** retry_round))
        n_retry = len(failed)
        retry_stocks = sum(len(batches[i]) for i in failed)
        retry_items = retry_stocks * len(table_list)
        tqdm.write(
            f"  🔄 财务数据重试第 {retry_round}/{max_retries} 轮: "
            f"{n_retry} 个批次 ({retry_stocks} 只), 超时 {retry_timeout}s"
        )
        logger.info(
            "财务数据重试第 %d 轮: %d 个批次 (%d 只), 超时 %ds",
            retry_round, n_retry, retry_stocks, retry_timeout,
        )
        retry_pbar = tqdm(total=retry_items, desc=f"财务 重试{retry_round}", unit="项")
        r_ok, r_fail, r_to, still_failed, interrupted = _run_financial_batches(
            batches, failed, table_list, retry_timeout, delay, retry_pbar, f"财务 重试{retry_round}",
        )
        ok += r_ok
        failed = still_failed

    # 最终修正计数（含缓存跳过的股票）
    n_cached = n_original - len(stocks)
    final_fail_stocks = sum(len(batches[i]) for i in failed)
    ok = len(stocks) - final_fail_stocks if not interrupted else ok
    ok += n_cached  # 缓存跳过的也计入成功
    fail = final_fail_stocks
    to = len(failed)

    logger.info("财务数据完成: 成功 %d (缓存 %d), 失败 %d (超时 %d)", ok, n_cached, fail, to)
    if failed:
        logger.warning("财务数据最终失败批次索引: %s", failed)
        tqdm.write(f"  财务数据最终失败批次索引: {failed}")

    return {"ok": ok, "fail": fail, "timeout": to}


# ── v2 新增：缓存探测与分组 ───────────────────────────────────

def probe_local_dates(stocks: list[str], period: str) -> dict[str, str]:
    """批量探测每只股票本地缓存的最新数据日期。

    对全部股票分批调用 get_local_data(count=1)，
    每批 200 只，每只仅返回最后 1 条记录。

    Returns:
        {stock_code: "YYYYMMDD"} — 无本地数据的股票不在字典中。
    """
    result: dict[str, str] = {}
    probe_pbar = tqdm(total=len(stocks), desc="探测本地缓存", unit="只")
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
        probe_pbar.update(len(batch))
    probe_pbar.close()
    return result


def group_stocks_by_date(
    stocks: list[str],
    local_dates: dict[str, str],
) -> list[tuple[str, list[str]]]:
    """按本地缓存最新日期分组。

    有缓存的股票: start_time = last_date - SAFETY_OVERLAP_DAYS
    无缓存的股票: start_time = "" (全量)

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


# ── 年度分段下载支持 ──────────────────────────────────────────

def probe_year_coverage(
    stocks: list[str], period: str, since_year: int,
) -> dict[int, set[str]]:
    """探测每个年份中哪些股票已有本地缓存。

    对 [since_year, current_year] 范围内的每个年份，
    分批调用 get_local_data(count=1) 检测是否有数据。

    Returns:
        {year: {有缓存数据的 stock_code 集合}}
    """
    current_year = datetime.now().year
    years = list(range(since_year, current_year + 1))
    coverage: dict[int, set[str]] = {y: set() for y in years}
    total_probes = len(stocks) * len(years)
    probe_pbar = tqdm(total=total_probes, desc="探测年度缓存", unit="只")
    for year in years:
        for batch in make_batches(stocks, PROBE_BATCH_SIZE):
            try:
                data = xtdata.get_local_data(
                    field_list=[], stock_list=batch, period=period,
                    start_time=f"{year}0101", end_time=f"{year}1231", count=1,
                )
                for stock, df in data.items():
                    if df is not None and not df.empty:
                        coverage[year].add(stock)
            except Exception as exc:
                logger.warning("年度缓存探测失败 (year=%d): %s", year, exc)
            probe_pbar.update(len(batch))
    probe_pbar.close()
    return coverage


def build_year_groups(
    stocks: list[str],
    period: str,
    since_year: int,
    full: bool,
) -> list[tuple[str, str, list[str]]]:
    """构建年度下载任务列表，从最近年份到最远年份排列。

    full=True 时跳过探测，视为全部无缓存。

    Returns:
        [(start_time, end_time, [stocks]), ...]
        当前年 end_time=""，历史年 end_time="YYYY1231"。
    """
    current_year = datetime.now().year
    years = list(range(since_year, current_year + 1))

    if full:
        # --full 模式: 不探测，全部视为无缓存
        coverage: dict[int, set[str]] = {y: set() for y in years}
    else:
        tqdm.write(f"\n探测 {period} 年度缓存 ({since_year}-{current_year})...")
        coverage = probe_year_coverage(stocks, period, since_year)

    # 按每只股票的已缓存年份数排序：缓存最少（缺口最大）的优先下载
    stock_cached_years = {
        s: sum(1 for y in years if s in coverage.get(y, set()))
        for s in stocks
    }

    groups: list[tuple[str, str, list[str]]] = []
    # 从最近年份到最远年份
    for year in reversed(years):
        cached = coverage.get(year, set())
        need_download = sorted(
            [s for s in stocks if s not in cached],
            key=lambda s: stock_cached_years[s],
        )
        if year == current_year:
            end_time = ""  # 当前年获取最新数据
            range_label = f"{year}0101 ~ 至今"
        else:
            end_time = f"{year}1231"
            range_label = f"{year}0101 ~ {year}1231"
        if not need_download:
            tqdm.write(f"  · {year}: 全部 {len(stocks)} 只已有缓存，跳过")
            logger.info("年度 %d: 全部 %d 只已有缓存，跳过", year, len(stocks))
        else:
            skipped = len(stocks) - len(need_download)
            tqdm.write(
                f"  · {year} ({range_label}): "
                f"需下载 {len(need_download)} 只, 跳过 {skipped} 只"
            )
            logger.info(
                "年度 %d (%s): 需下载 %d 只, 跳过 %d 只",
                year, range_label, len(need_download), skipped,
            )
            groups.append((f"{year}0101", end_time, need_download))

    return groups


# ── v2 新增：分组下载主函数 ───────────────────────────────────

def download_kline_v2(
    stocks: list[str],
    periods: list[str],
    full: bool,
    max_retries: int,
    since_year: int | None = None,
) -> dict[str, dict[str, int]]:
    """逐只下载 K 线数据。

    三种模式:
    A. --since YYYY: 按年度分段下载，自动跳过已缓存年份
    B. --full (无 --since): 所有股票统一 start_time=""
    C. 默认: 逐股精准增量，按日期分组下载

    Returns:
        {period: {"ok": n, "fail": n, "timeout": n, "date_groups": n}}
    """
    results: dict[str, dict[str, int]] = {}
    client = xtdata.get_client()

    for period in periods:
        effective_timeout = STOCK_TIMEOUT.get(period, 10)
        tqdm.write(f"  周期 {period} 单只超时: {effective_timeout}s")
        logger.info("K线 %s 单只超时: %ds", period, effective_timeout)

        # 年度模式不重试：失败的股票重跑命令会自动跳过已缓存数据
        effective_retries = 0 if since_year is not None else max_retries

        if since_year is not None:
            # 模式 A: 年度分段下载 (--since)
            # 外层已通过 probe_year_coverage 跳过已缓存年份，
            # 无需 xtquant 内部再做增量扫描，用 None 让其自动决定
            # (start_time 非空时自动 False，省去缓存扫描开销)
            date_groups = build_year_groups(stocks, period, since_year, full)
            incrementally = None
        elif full:
            # 模式 B: 传统全量 (--full, 无 --since)
            date_groups = [("", "", stocks)]
            incrementally = None
        else:
            # 模式 C: 逐股精准增量，从上次缓存日期续下，必须增量
            incrementally = True
            tqdm.write(f"\n探测 {period} 本地缓存...")
            local_dates = probe_local_dates(stocks, period)
            today_str = datetime.now().strftime("%Y%m%d")
            # 按缺口天数降序排列：无缓存 > 缓存最旧 > 缓存最新
            def _gap_sort_key(s: str) -> int:
                d = local_dates.get(s)
                if not d:
                    return 999999  # 无缓存，缺口最大
                return (datetime.strptime(today_str, "%Y%m%d") - datetime.strptime(d, "%Y%m%d")).days
            sorted_stocks = sorted(stocks, key=_gap_sort_key, reverse=True)
            # 每只股票用自己精确的 start_time
            date_groups = []
            for s in sorted_stocks:
                d = local_dates.get(s)
                if d:
                    overlap_dt = datetime.strptime(d, "%Y%m%d") - timedelta(days=SAFETY_OVERLAP_DAYS)
                    st = overlap_dt.strftime("%Y%m%d")
                else:
                    st = ""
                date_groups.append((st, "", [s]))
            # 打印摘要
            n_no_cache = sum(1 for s in sorted_stocks if s not in local_dates)
            n_cached = len(sorted_stocks) - n_no_cache
            if n_no_cache:
                tqdm.write(f"  · {n_no_cache} 只无缓存 (全量下载)")
            if n_cached:
                oldest = min(local_dates.values())
                newest = max(local_dates.values())
                tqdm.write(f"  · {n_cached} 只有缓存 (最旧 {oldest}, 最新 {newest})")

        n_date_groups = len(date_groups)

        # 按组逐只下载
        total_stocks = sum(len(g) for _, _, g in date_groups)
        pbar = tqdm(total=total_stocks, desc=f"K线 {period}", unit="只")
        total_ok = 0
        total_fail = 0
        total_to = 0
        interrupted = False

        for start_time, end_time, group_stocks in date_groups:
            all_indices = list(range(len(group_stocks)))
            st_label = start_time or "(全量)"
            et_label = end_time or "(至今)"
            logger.info(
                "开始下载 K 线 %s，组 start=%s end=%s，共 %d 只, 超时 %ds",
                period, st_label, et_label, len(group_stocks), effective_timeout,
            )

            ok, fail, to, failed, interrupted = _run_kline_downloads(
                client, group_stocks, all_indices, period, start_time, end_time,
                incrementally, effective_timeout, pbar, f"K线 {period}",
            )

            # 自动重试失败股票
            for retry_round in range(1, effective_retries + 1):
                if not failed or interrupted:
                    break
                retry_timeout = int(effective_timeout * (1.5 ** retry_round))
                n_retry = len(failed)
                tqdm.write(
                    f"  🔄 K线 {period} 重试第 {retry_round}/{effective_retries} 轮: "
                    f"{n_retry} 只, 超时 {retry_timeout}s"
                )
                logger.info(
                    "K线 %s 重试第 %d 轮: %d 只, 超时 %ds",
                    period, retry_round, n_retry, retry_timeout,
                )
                retry_pbar = tqdm(total=n_retry, desc=f"K线 {period} 重试{retry_round}", unit="只")
                r_ok, r_fail, r_to, still_failed, interrupted = _run_kline_downloads(
                    client, group_stocks, failed, period, start_time, end_time,
                    incrementally, retry_timeout, retry_pbar,
                    f"K线 {period} 重试{retry_round}",
                )
                retry_pbar.close()
                ok += r_ok
                failed = still_failed

            final_fail = len(failed)
            ok = len(group_stocks) - final_fail if not interrupted else ok
            total_ok += ok
            total_fail += final_fail
            total_to += len(failed)

            if failed:
                failed_codes = [group_stocks[i] for i in failed[:10]]
                suffix = f" ...等 {len(failed)} 只" if len(failed) > 10 else ""
                logger.warning("K线 %s (start=%s) 最终失败: %s%s", period, st_label, failed_codes, suffix)
                tqdm.write(f"  {period} (start={st_label}) 失败 {len(failed)} 只")

            if interrupted:
                break

        pbar.close()
        results[period] = {
            "ok": total_ok, "fail": total_fail, "timeout": total_to,
            "date_groups": n_date_groups,
        }
        logger.info(
            "K线 %s 完成: 成功 %d, 失败 %d (超时 %d), 日期组 %d",
            period, total_ok, total_fail, total_to, n_date_groups,
        )
        if interrupted:
            break

    return results


# ── CLI ───────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="逐股精准增量下载沪深 A 股历史行情 + 财务数据 (v2)",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        default=False,
        help="强制全量下载（跳过缓存探测，所有股票 start_time=\"\"）",
    )
    parser.add_argument(
        "--since",
        type=int,
        default=None,
        metavar="YYYY",
        help="按年度分段下载，从指定年份开始 (如 --since 2025 下载 2025 至今)",
    )
    parser.add_argument(
        "--periods",
        default="1d,5m,1m",
        help="K 线周期，逗号分隔 (默认: 1d,5m,1m)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=20,
        help="财务数据每批股票数量 (默认: 20，K 线逐只下载不受此参数影响)",
    )
    parser.add_argument(
        "--tables",
        default="Balance,Income,CashFlow",
        help="财务报表类型，逗号分隔 (默认: Balance,Income,CashFlow)",
    )
    parser.add_argument(
        "--skip-kline",
        action="store_true",
        help="跳过 K 线下载",
    )
    parser.add_argument(
        "--skip-financial",
        action="store_true",
        help="跳过财务数据下载",
    )
    parser.add_argument(
        "--sectors",
        default=DEFAULT_SECTORS,
        help=f"目标板块，逗号分隔 (默认: {DEFAULT_SECTORS})",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="财务数据每批下载超时秒数 (默认: 120，K 线超时由 STOCK_TIMEOUT 常量控制)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.2,
        help="财务数据批次间延迟秒数 (默认: 0.2，K 线逐只下载无延迟)",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=2,
        help="超时批次最大自动重试次数 (默认: 2)",
    )
    return parser.parse_args()


def print_summary(
    total: int,
    elapsed: float,
    kline_results: dict[str, dict[str, int]] | None,
    financial_result: dict[str, int] | None,
    full: bool,
    since_year: int | None = None,
    state_saved: bool = False,
) -> None:
    """打印下载结果汇总（含探测分组信息）。"""
    minutes = elapsed / 60
    has_failure = False

    print()
    print("=" * 60)
    print("下载完成 — 结果汇总")
    print("=" * 60)
    print(f"股票总数: {total}")
    print(f"耗时: {elapsed:.1f} 秒 ({minutes:.1f} 分钟)")

    if kline_results:
        print()
        print("K线数据:")
        for period, counts in kline_results.items():
            n_groups = counts.get("date_groups", 0)
            if since_year is not None:
                mode_info = f"年度分段 (since {since_year}): {n_groups} 个年度组"
            elif full:
                mode_info = "全量"
            elif n_groups > 0:
                mode_info = f"精准增量: {n_groups} 个日期组"
            else:
                mode_info = ""
            if counts["fail"] == 0:
                print(f"  {period}: 成功 {counts['ok']}, OK ({mode_info})")
            else:
                has_failure = True
                timeout_info = f" (超时 {counts['timeout']})" if counts.get("timeout") else ""
                print(f"  {period}: 成功 {counts['ok']}, 失败 {counts['fail']}{timeout_info} ({mode_info})")

    if financial_result:
        print()
        if financial_result["fail"] == 0:
            print(f"财务数据: 成功 {financial_result['ok']}, OK")
        else:
            has_failure = True
            timeout_info = f" (超时 {financial_result['timeout']})" if financial_result.get("timeout") else ""
            print(
                f"财务数据: 成功 {financial_result['ok']}, "
                f"失败 {financial_result['fail']}{timeout_info}"
            )

    if has_failure:
        print()
        print("⚠️  部分批次下载失败，请检查日志后重试")

    if state_saved:
        print()
        print(f"状态文件: {STATE_FILE}")

    print("=" * 60)


# ── 入口 ──────────────────────────────────────────────────────

def main() -> None:
    args = parse_args()

    logger.info("日志文件: %s", _log_file)
    print(f"日志文件: {_log_file}")

    # ── 状态管理 ──
    state = load_state()

    # 1. 获取股票列表（支持多板块合并去重）
    sectors = [s.strip() for s in args.sectors.split(",")]
    stocks: list[str] = []
    seen: set[str] = set()
    for sector in sectors:
        codes = xtdata.get_stock_list_in_sector(sector)
        logger.info("板块 [%s] 返回 %d 只", sector, len(codes))
        for c in codes:
            if c not in seen:
                seen.add(c)
                stocks.append(c)
    if not stocks:
        logger.error("板块 %s 返回空列表", sectors)
        print(f"错误: 板块 {sectors} 返回空列表，请检查 xtdata 连接状态")
        sys.exit(1)
    print(f"板块 {sectors} 共 {len(stocks)} 只标的")

    periods = [p.strip() for p in args.periods.split(",")]
    tables = [t.strip() for t in args.tables.split(",")]

    # 打印模式信息
    if args.since is not None and args.full:
        print(f"模式: 年度强制全量下载 (--since {args.since} --full)")
        logger.info("年度强制全量模式 (--since %d --full)", args.since)
    elif args.since is not None:
        print(f"模式: 年度分段下载 (--since {args.since}，自动跳过已缓存年份)")
        logger.info("年度分段下载模式 (--since %d)", args.since)
    elif args.full:
        print("模式: 强制全量下载 (--full)")
        logger.info("强制全量模式 (--full)")
    else:
        print("模式: 逐股精准增量 (基于本地缓存探测)")
        logger.info("逐股精准增量模式")

    logger.info("超时: %d秒/批, 延迟: %.1f秒/批, 最大重试: %d", args.timeout, args.delay, args.max_retries)
    print(f"超时: {args.timeout}秒/批, 批次间延迟: {args.delay}秒, 失败自动重试: {args.max_retries} 轮")

    print()
    t0 = time.time()
    kline_results = None
    financial_result = None
    today = datetime.now().strftime("%Y%m%d")
    now_iso = datetime.now().isoformat(timespec="seconds")

    try:
        # 2. K 线下载
        if not args.skip_kline:
            print(f"开始下载 K 线数据 (周期: {', '.join(periods)})...")
            kline_results = download_kline_v2(
                stocks, periods,
                full=args.full,
                max_retries=args.max_retries,
                since_year=args.since,
            )
        else:
            print("跳过 K 线下载")

        # 3. 财务数据下载
        if not args.skip_financial:
            print(f"\n开始下载财务数据 (报表: {', '.join(tables)})...")
            financial_result = download_financial(
                stocks, tables, args.batch_size,
                timeout=args.timeout, delay=args.delay, max_retries=args.max_retries,
                full=args.full,
            )
        else:
            print("跳过财务数据下载")
    except KeyboardInterrupt:
        logger.warning("用户中断 (Ctrl+C)")
        print("\n\n用户中断 (Ctrl+C)")

    elapsed = time.time() - t0

    # ── 更新状态 ──
    if kline_results:
        for period, counts in kline_results.items():
            task_key = f"kline:{period}"
            old = state.tasks.get(task_key)
            ts = TaskState(
                last_success_date=old.last_success_date if old else "",
                last_run_iso=now_iso,
                stock_count=len(stocks),
                ok=counts["ok"],
                fail=counts["fail"],
            )
            if counts["fail"] == 0:
                ts.last_success_date = today
            state.tasks[task_key] = ts
    if financial_result:
        task_key = "financial"
        old = state.tasks.get(task_key)
        ts = TaskState(
            last_success_date=old.last_success_date if old else "",
            last_run_iso=now_iso,
            stock_count=len(stocks),
            ok=financial_result["ok"],
            fail=financial_result["fail"],
        )
        if financial_result["fail"] == 0:
            ts.last_success_date = today
        state.tasks[task_key] = ts
    save_state(state)

    # 4. 汇总（即使中断也打印已完成的部分）
    print_summary(
        len(stocks), elapsed, kline_results, financial_result,
        full=args.full, since_year=args.since, state_saved=True,
    )
    logger.info("完成，耗时 %.1f 秒", elapsed)

    # xtdata 下载线程是非 daemon 线程，中断后仍在后台运行，
    # 正常 sys.exit() 会等待这些线程完成导致卡死，需强制退出。
    if _interrupted:
        os._exit(0)


if __name__ == "__main__":
    main()

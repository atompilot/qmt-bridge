"""逐股精准增量下载沪深 A 股历史 K 线 + 财务数据。

基于本地缓存探测，每只股票从各自的最新缓存日期开始增量下载。
首次运行自动全量，后续运行自动精准增量。

用法:
    python scripts/download_all.py [OPTIONS]
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

# future.result(timeout=N) 在 Windows 上会长时间阻塞主线程导致 Ctrl+C 无响应，
# 改用短轮询让 Python 每隔 POLL_INTERVAL 秒有机会处理 KeyboardInterrupt。
POLL_INTERVAL = 0.5

try:
    from tqdm import tqdm
except ImportError:
    print("错误: 需要 tqdm 依赖，请先执行: pip install tqdm>=4.60")
    print("  或: pip install -e \".[scripts]\"")
    sys.exit(1)

# 分钟级周期数据量远大于日线，需要更长超时；乘以基准 --timeout
PERIOD_TIMEOUT_SCALE: dict[str, float] = {
    "1m": 3.0,
    "5m": 2.5,
    "15m": 2.0,
    "30m": 1.5,
    "60m": 1.5,
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
DEFAULT_SECTORS = "沪深A股,沪深ETF,沪深指数,沪深转债"

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


def _make_kline_cb(
    flag: list[bool], codes: list[str], fail_count: int, timeout_count: int, pbar: tqdm,
) -> callable:
    """创建 K 线下载回调，用于更新 tqdm 进度条。"""
    n_codes = len(codes)
    def _on_progress(data: dict) -> None:
        if flag[0]:
            return
        finished = data.get("finished", 0)
        total = data.get("total", 0)
        if total > 0:
            stock_idx = min(int(finished * n_codes / total), n_codes) - 1
        else:
            stock_idx = -1
        parts = [f"批内 {finished}/{total}"]
        if 0 <= stock_idx < n_codes:
            parts.append(codes[stock_idx])
        if fail_count or timeout_count:
            parts.append(f"失败:{fail_count} 超时:{timeout_count}")
        pbar.set_postfix_str(" | ".join(parts), refresh=True)
    return _on_progress


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


def _run_kline_batches(
    batches: list[list[str]],
    batch_indices: list[int],
    period: str,
    start_time: str,
    timeout: int,
    delay: float,
    pbar: tqdm,
    label: str,
) -> tuple[int, int, int, list[int], bool]:
    """执行一轮 K 线批次下载。

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
        cancelled = [False]
        pbar.set_description(f"{label} [{seq+1}/{n_total}批]")

        executor = ThreadPoolExecutor(max_workers=1)
        try:
            future = executor.submit(
                xtdata.download_history_data2,
                stock_list=batch,
                period=period,
                start_time=start_time,
                end_time="",
                callback=_make_kline_cb(cancelled, batch, fail_count, timeout_count, pbar),
                incrementally=True,
            )
            _wait_future(future, timeout)
            ok_count += len(batch)
            logger.debug("K线 %s 批次 %d 成功 (%d 只)", period, idx+1, len(batch))
        except FutureTimeoutError:
            cancelled[0] = True
            timeout_count += 1
            fail_count += len(batch)
            failed_indices.append(idx)
            logger.error("K线 %s 批次 %d 超时 (%d秒, %d 只)", period, idx+1, timeout, len(batch))
            tqdm.write(f"  ⚠ 批次 {idx+1} 超时 ({timeout}s, {len(batch)} 只)")
        except KeyboardInterrupt:
            global _interrupted
            _interrupted = True
            cancelled[0] = True
            executor.shutdown(wait=False, cancel_futures=True)
            pbar.close()
            logger.warning("K线 %s 被用户中断", period)
            tqdm.write(f"\n  用户中断，K线 {period} 本轮已完成 {ok_count} 只")
            return ok_count, fail_count, timeout_count, failed_indices, True
        except Exception as exc:
            cancelled[0] = True
            fail_count += len(batch)
            failed_indices.append(idx)
            logger.error("K线 %s 批次 %d 失败 (%d 只): %s", period, idx+1, len(batch), exc)
            tqdm.write(f"  ⚠ 批次 {idx+1} 失败 ({len(batch)} 只): {exc}")
        finally:
            executor.shutdown(wait=False, cancel_futures=True)
            pbar.update(len(batch))

        if delay > 0 and seq < n_total - 1:
            time.sleep(delay)
    else:
        pbar.close()

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


def download_financial(
    stocks: list[str],
    table_list: list[str],
    batch_size: int,
    timeout: int = 120,
    delay: float = 0.2,
    max_retries: int = 2,
) -> dict[str, int]:
    """下载财务数据，返回 {"ok": n, "fail": n, "timeout": n}。

    通过 callback 实现逐项（股票 × 报表）粒度的进度更新。
    每批下载有超时保护，批次间有延迟以缓解服务端压力。
    超时失败的批次会自动重试，每轮重试超时再增加 50%。
    """
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

    # 最终修正计数
    final_fail_stocks = sum(len(batches[i]) for i in failed)
    ok = len(stocks) - final_fail_stocks if not interrupted else ok
    fail = final_fail_stocks
    to = len(failed)

    logger.info("财务数据完成: 成功 %d, 失败 %d (其中超时 %d)", ok, fail, to)
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


# ── v2 新增：分组下载主函数 ───────────────────────────────────

def download_kline_v2(
    stocks: list[str],
    periods: list[str],
    full: bool,
    batch_size: int,
    timeout: int,
    delay: float,
    max_retries: int,
) -> dict[str, dict[str, int]]:
    """按逐股精准增量策略下载 K 线数据。

    --full 模式: 所有股票统一 start_time=""
    默认模式: 对每个 period 探测本地缓存，按日期分组后批量下载。

    Returns:
        {period: {"ok": n, "fail": n, "timeout": n, "date_groups": n}}
    """
    results: dict[str, dict[str, int]] = {}

    for period in periods:
        scale = PERIOD_TIMEOUT_SCALE.get(period, 1.0)
        effective_timeout = int(timeout * scale)
        if scale > 1.0:
            tqdm.write(f"  周期 {period} 超时自动调整: {timeout}s × {scale} = {effective_timeout}s")
            logger.info("K线 %s 超时调整: %d × %.1f = %d", period, timeout, scale, effective_timeout)

        if full:
            # --full: 所有股票统一全量
            date_groups = [("", stocks)]
        else:
            # 默认: 逐股精准增量
            tqdm.write(f"\n探测 {period} 本地缓存...")
            local_dates = probe_local_dates(stocks, period)
            date_groups = group_stocks_by_date(stocks, local_dates)
            # 打印分组摘要
            for st, grp in date_groups:
                label = f"起始 {st}" if st else "全量 (无本地缓存)"
                tqdm.write(f"  · {len(grp)} 只 → {label}")

        n_date_groups = len(date_groups)

        # 按组下载
        total_stocks = sum(len(g) for _, g in date_groups)
        pbar = tqdm(total=total_stocks, desc=f"K线 {period}", unit="只")
        total_ok = 0
        total_fail = 0
        total_to = 0
        interrupted = False

        for start_time, group_stocks in date_groups:
            batches = make_batches(group_stocks, batch_size)
            all_indices = list(range(len(batches)))
            n_batches = len(batches)
            st_label = start_time or "(全量)"
            logger.info(
                "开始下载 K 线 %s，组 start=%s，共 %d 批 (%d 只), 超时 %ds",
                period, st_label, n_batches, len(group_stocks), effective_timeout,
            )

            ok, fail, to, failed, interrupted = _run_kline_batches(
                batches, all_indices, period, start_time,
                effective_timeout, delay, pbar, f"K线 {period}",
            )

            # 自动重试失败批次
            for retry_round in range(1, max_retries + 1):
                if not failed or interrupted:
                    break
                retry_timeout = int(effective_timeout * (1.5 ** retry_round))
                n_retry = len(failed)
                retry_stocks = sum(len(batches[i]) for i in failed)
                tqdm.write(
                    f"  🔄 K线 {period} 重试第 {retry_round}/{max_retries} 轮: "
                    f"{n_retry} 个批次 ({retry_stocks} 只), 超时 {retry_timeout}s"
                )
                logger.info(
                    "K线 %s 重试第 %d 轮: %d 个批次 (%d 只), 超时 %ds",
                    period, retry_round, n_retry, retry_stocks, retry_timeout,
                )
                retry_pbar = tqdm(total=retry_stocks, desc=f"K线 {period} 重试{retry_round}", unit="只")
                r_ok, r_fail, r_to, still_failed, interrupted = _run_kline_batches(
                    batches, failed, period, start_time, retry_timeout, delay, retry_pbar,
                    f"K线 {period} 重试{retry_round}",
                )
                ok += r_ok
                failed = still_failed

            final_fail = sum(len(batches[i]) for i in failed)
            ok = len(group_stocks) - final_fail if not interrupted else ok
            total_ok += ok
            total_fail += final_fail
            total_to += len(failed)

            if failed:
                logger.warning("K线 %s (start=%s) 最终失败批次索引: %s", period, st_label, failed)
                tqdm.write(f"  {period} (start={st_label}) 最终失败批次索引: {failed}")

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
        "--periods",
        default="1d,5m,1m",
        help="K 线周期，逗号分隔 (默认: 1d,5m,1m)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="每批股票数量 (默认: 50)",
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
        help="每批下载超时秒数 (默认: 120)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.2,
        help="批次间延迟秒数，缓解服务端压力 (默认: 0.2)",
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
            if full:
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
    if args.full:
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
                batch_size=args.batch_size,
                timeout=args.timeout,
                delay=args.delay,
                max_retries=args.max_retries,
            )
        else:
            print("跳过 K 线下载")

        # 3. 财务数据下载
        if not args.skip_financial:
            print(f"\n开始下载财务数据 (报表: {', '.join(tables)})...")
            financial_result = download_financial(
                stocks, tables, args.batch_size,
                timeout=args.timeout, delay=args.delay, max_retries=args.max_retries,
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
        full=args.full, state_saved=True,
    )
    logger.info("完成，耗时 %.1f 秒", elapsed)

    # xtdata 下载线程是非 daemon 线程，中断后仍在后台运行，
    # 正常 sys.exit() 会等待这些线程完成导致卡死，需强制退出。
    if _interrupted:
        os._exit(0)


if __name__ == "__main__":
    main()

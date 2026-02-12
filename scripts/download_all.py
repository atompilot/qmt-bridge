"""全量下载沪深 A 股历史 K 线 + 财务数据到本地缓存。

独立于服务端，直接调用 xtdata，支持增量模式和 tqdm 进度展示。

用法:
    python scripts/download_all.py [OPTIONS]
    just download-all [OPTIONS]
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from datetime import datetime, timedelta
from pathlib import Path

from xtquant import xtdata

try:
    from tqdm import tqdm
except ImportError:
    print("错误: 需要 tqdm 依赖，请先执行: pip install tqdm>=4.60")
    print("  或: pip install -e \".[scripts]\"")
    sys.exit(1)

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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="全量下载沪深 A 股历史行情 + 财务数据",
    )
    parser.add_argument(
        "--periods",
        default="1d,5m",
        help="K 线周期，逗号分隔 (默认: 1d,5m)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=None,
        help="增量模式：仅下载最近 N 天 (省略则全量)",
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
        "--sector",
        default="沪深A股",
        help="目标板块 (默认: 沪深A股)",
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
    return parser.parse_args()


def make_batches(lst: list, size: int) -> list[list]:
    """将列表按 size 切分为子列表。"""
    return [lst[i : i + size] for i in range(0, len(lst), size)]


def download_kline(
    stocks: list[str],
    periods: list[str],
    start_time: str,
    batch_size: int,
    timeout: int = 120,
    delay: float = 0.2,
) -> dict[str, dict[str, int]]:
    """下载 K 线数据，返回 {period: {"ok": n, "fail": n, "timeout": n}}。

    通过 callback 实现逐只股票粒度的进度更新。
    每批下载有超时保护，批次间有延迟以缓解服务端压力。
    xtdata 会根据 start_time 自动决定是否增量下载。
    """
    batches = make_batches(stocks, batch_size)
    results: dict[str, dict[str, int]] = {}

    for period in periods:
        ok_count = 0
        fail_count = 0
        timeout_count = 0
        failed_batches: list[int] = []

        n_batches = len(batches)
        logger.info("开始下载 K 线 %s，共 %d 批 (%d 只)", period, n_batches, len(stocks))
        pbar = tqdm(total=len(stocks), desc=f"K线 {period}", unit="只")

        for idx, batch in enumerate(batches):
            cancelled = [False]   # 超时/失败后禁止回调继续更新进度条
            pbar.set_description(f"K线 {period} [{idx+1}/{n_batches}批]")

            def _make_cb(flag: list[bool], codes: list[str]) -> callable:
                n_codes = len(codes)
                def _on_progress(data: dict) -> None:
                    if flag[0]:
                        return
                    finished = data.get("finished", 0)
                    total = data.get("total", 0)
                    # 用比例估算当前下载到第几只股票
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

            executor = ThreadPoolExecutor(max_workers=1)
            try:
                future = executor.submit(
                    xtdata.download_history_data2,
                    stock_list=batch,
                    period=period,
                    start_time=start_time,
                    end_time="",
                    callback=_make_cb(cancelled, batch),
                )
                future.result(timeout=timeout)
                ok_count += len(batch)
                logger.debug("K线 %s 批次 %d/%d 成功 (%d 只)", period, idx+1, n_batches, len(batch))
            except FutureTimeoutError:
                cancelled[0] = True
                timeout_count += 1
                fail_count += len(batch)
                failed_batches.append(idx)
                logger.error(
                    "K线 %s 批次 %d/%d 超时 (%d秒, %d 只)",
                    period, idx+1, n_batches, timeout, len(batch),
                )
                tqdm.write(
                    f"  ⚠ 批次 {idx+1}/{n_batches} 超时 ({timeout}s, {len(batch)} 只)"
                )
            except Exception as exc:
                cancelled[0] = True
                fail_count += len(batch)
                failed_batches.append(idx)
                logger.error("K线 %s 批次 %d/%d 失败 (%d 只): %s", period, idx+1, n_batches, len(batch), exc)
                tqdm.write(f"  ⚠ 批次 {idx+1}/{n_batches} 失败 ({len(batch)} 只): {exc}")
            finally:
                executor.shutdown(wait=False, cancel_futures=True)
                pbar.update(len(batch))

            # 批次间延迟，缓解 xtdata 服务端压力
            if delay > 0 and idx < n_batches - 1:
                time.sleep(delay)

        pbar.close()
        results[period] = {"ok": ok_count, "fail": fail_count, "timeout": timeout_count}
        logger.info(
            "K线 %s 完成: 成功 %d, 失败 %d (其中超时 %d)",
            period, ok_count, fail_count, timeout_count,
        )
        if failed_batches:
            logger.warning("K线 %s 失败批次索引: %s", period, failed_batches)
            tqdm.write(f"  {period} 失败批次索引: {failed_batches}")

    return results


def download_financial(
    stocks: list[str],
    table_list: list[str],
    batch_size: int,
    timeout: int = 120,
    delay: float = 0.2,
) -> dict[str, int]:
    """下载财务数据，返回 {"ok": n, "fail": n, "timeout": n}。

    通过 callback 实现逐项（股票 × 报表）粒度的进度更新。
    每批下载有超时保护，批次间有延迟以缓解服务端压力。
    """
    batches = make_batches(stocks, batch_size)
    total_items = len(stocks) * len(table_list)
    ok_count = 0
    fail_count = 0
    timeout_count = 0
    failed_batches: list[int] = []

    n_batches = len(batches)
    logger.info(
        "开始下载财务数据，共 %d 批 (%d 只 × %d 表 = %d 项)",
        n_batches, len(stocks), len(table_list), total_items,
    )
    pbar = tqdm(total=total_items, desc="财务", unit="项")

    for idx, batch in enumerate(batches):
        batch_items = len(batch) * len(table_list)
        cancelled = [False]
        pbar.set_description(f"财务 [{idx+1}/{n_batches}批]")

        def _make_cb(flag: list[bool], codes: list[str], tables: list[str]) -> callable:
            n_codes = len(codes)
            n_tables = len(tables)
            def _on_progress(data: dict) -> None:
                if flag[0]:
                    return
                finished = data.get("finished", 0)
                total = data.get("total", 0)
                # 用比例估算当前下载到第几只股票的第几张表
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

        executor = ThreadPoolExecutor(max_workers=1)
        try:
            future = executor.submit(
                xtdata.download_financial_data2,
                stock_list=batch,
                table_list=table_list,
                callback=_make_cb(cancelled, batch, table_list),
            )
            future.result(timeout=timeout)
            ok_count += len(batch)
            logger.debug("财务数据批次 %d/%d 成功 (%d 只)", idx+1, n_batches, len(batch))
        except FutureTimeoutError:
            cancelled[0] = True
            timeout_count += 1
            fail_count += len(batch)
            failed_batches.append(idx)
            logger.error(
                "财务数据批次 %d/%d 超时 (%d秒, %d 只)",
                idx+1, n_batches, timeout, len(batch),
            )
            tqdm.write(
                f"  ⚠ 批次 {idx+1}/{n_batches} 超时 ({timeout}s, {len(batch)} 只)"
            )
        except Exception as exc:
            cancelled[0] = True
            fail_count += len(batch)
            failed_batches.append(idx)
            logger.error("财务数据批次 %d/%d 失败 (%d 只): %s", idx+1, n_batches, len(batch), exc)
            tqdm.write(f"  ⚠ 批次 {idx+1}/{n_batches} 失败 ({len(batch)} 只): {exc}")
        finally:
            executor.shutdown(wait=False, cancel_futures=True)
            pbar.update(batch_items)

        # 批次间延迟，缓解 xtdata 服务端压力
        if delay > 0 and idx < n_batches - 1:
            time.sleep(delay)

    pbar.close()
    logger.info(
        "财务数据完成: 成功 %d, 失败 %d (其中超时 %d)",
        ok_count, fail_count, timeout_count,
    )
    if failed_batches:
        logger.warning("财务数据失败批次索引: %s", failed_batches)
        tqdm.write(f"  财务数据失败批次索引: {failed_batches}")

    return {"ok": ok_count, "fail": fail_count, "timeout": timeout_count}


def print_summary(
    total: int,
    elapsed: float,
    kline_results: dict[str, dict[str, int]] | None,
    financial_result: dict[str, int] | None,
) -> None:
    """打印下载结果汇总。"""
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
            if counts["fail"] == 0:
                print(f"  {period}: 成功 {counts['ok']}, OK")
            else:
                has_failure = True
                timeout_info = f" (超时 {counts['timeout']})" if counts.get("timeout") else ""
                print(f"  {period}: 成功 {counts['ok']}, 失败 {counts['fail']}{timeout_info}")

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

    print("=" * 60)


def main() -> None:
    args = parse_args()

    logger.info("日志文件: %s", _log_file)
    print(f"日志文件: {_log_file}")

    # 1. 获取股票列表
    print(f"获取板块 [{args.sector}] 股票列表...")
    stocks: list[str] = xtdata.get_stock_list_in_sector(args.sector)
    if not stocks:
        logger.error("板块 [%s] 返回空列表", args.sector)
        print(f"错误: 板块 [{args.sector}] 返回空列表，请检查 xtdata 连接状态")
        sys.exit(1)
    logger.info("板块 [%s] 共 %d 只股票", args.sector, len(stocks))
    print(f"共 {len(stocks)} 只股票")

    # 计算 start_time
    if args.days is not None:
        start_time = (datetime.now() - timedelta(days=args.days)).strftime("%Y%m%d")
        logger.info("增量模式: 最近 %d 天, start_time=%s", args.days, start_time)
        print(f"增量模式: 下载最近 {args.days} 天 (起始: {start_time})")
    else:
        start_time = ""
        logger.info("全量模式")
        print("全量模式: 下载全部历史数据")

    periods = [p.strip() for p in args.periods.split(",")]
    tables = [t.strip() for t in args.tables.split(",")]

    logger.info("超时: %d秒/批, 延迟: %.1f秒/批", args.timeout, args.delay)
    print(f"超时: {args.timeout}秒/批, 批次间延迟: {args.delay}秒")

    print()
    t0 = time.time()

    # 2. K 线下载
    kline_results = None
    if not args.skip_kline:
        print(f"开始下载 K 线数据 (周期: {', '.join(periods)})...")
        kline_results = download_kline(
            stocks, periods, start_time, args.batch_size,
            timeout=args.timeout, delay=args.delay,
        )
    else:
        print("跳过 K 线下载")

    # 3. 财务数据下载
    financial_result = None
    if not args.skip_financial:
        print(f"\n开始下载财务数据 (报表: {', '.join(tables)})...")
        financial_result = download_financial(
            stocks, tables, args.batch_size,
            timeout=args.timeout, delay=args.delay,
        )
    else:
        print("跳过财务数据下载")

    elapsed = time.time() - t0

    # 4. 汇总
    print_summary(len(stocks), elapsed, kline_results, financial_result)
    logger.info("全部完成，耗时 %.1f 秒", elapsed)


if __name__ == "__main__":
    main()

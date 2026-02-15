"""诊断 xtdata BSON 断言崩溃的根因。

用子进程逐步测试，定位是哪些 xtdata 函数/数据导致崩溃。
"""

import subprocess
import sys
import textwrap


def run_test(label: str, code: str) -> bool:
    """在子进程中运行测试代码，返回是否成功。"""
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True, text=True, timeout=30,
        )
    except subprocess.TimeoutExpired:
        print(f"  {label}: TIMEOUT")
        return False
    ok = result.returncode == 0
    status = "OK" if ok else f"CRASH (exit={result.returncode})"
    print(f"  {label}: {status}")
    if ok and result.stdout.strip():
        print(f"    {result.stdout.strip()}")
    if not ok and result.stderr:
        lines = result.stderr.strip().splitlines()
        for line in lines[-2:]:
            print(f"    {line.strip()}")
    return ok


def main():
    print("=== xtdata BSON 断言崩溃诊断 ===\n")

    # 1. 基础连接
    print("1. 基础连接测试")
    run_test("import xtdata", "from xtquant import xtdata; print('ok')")
    run_test("get_stock_list_in_sector", textwrap.dedent("""\
        from xtquant import xtdata
        stocks = xtdata.get_stock_list_in_sector('沪深A股')
        print(f"沪深A股: {len(stocks)}只")
    """))

    # 2. get_local_data — 已确认即使 1 只股票也崩溃
    print("\n2. get_local_data (单只股票, count=1)")
    for period in ["1d", "5m", "1m"]:
        run_test(f"period={period}", textwrap.dedent(f"""\
            from xtquant import xtdata
            data = xtdata.get_local_data(field_list=[], stock_list=['000001.SZ'],
                period='{period}', start_time='', end_time='', count=1)
            print(f"ok, keys={{len(data)}}")
        """))

    # 3. get_market_data_ex — API 端点 /api/market/market_data_ex 用的接口
    print("\n3. get_market_data_ex (API 端点使用)")
    for period in ["1d", "5m"]:
        run_test(f"period={period}", textwrap.dedent(f"""\
            from xtquant import xtdata
            data = xtdata.get_market_data_ex(field_list=[], stock_list=['000001.SZ'],
                period='{period}', start_time='', end_time='', count=5)
            print(f"ok, keys={{len(data)}}")
        """))

    # 4. get_full_tick — API 端点 /api/market/full_tick 用的接口
    print("\n4. get_full_tick")
    run_test("1只", textwrap.dedent("""\
        from xtquant import xtdata
        data = xtdata.get_full_tick(code_list=['000001.SZ'])
        print(f"ok, keys={len(data)}")
    """))
    run_test("50只", textwrap.dedent("""\
        from xtquant import xtdata
        stocks = xtdata.get_stock_list_in_sector('沪深A股')[:50]
        data = xtdata.get_full_tick(code_list=stocks)
        print(f"ok, keys={len(data)}")
    """))

    # 5. get_sector_data / get_stock_list_in_sector — 并发崩溃场景用的接口
    print("\n5. get_stock_list_in_sector (服务端崩溃场景)")
    run_test("顺序4次", textwrap.dedent("""\
        from xtquant import xtdata
        for s in ['沪深A股', '沪深ETF', '上证指数', '深证指数']:
            r = xtdata.get_stock_list_in_sector(s)
            print(f"  {s}: {len(r)}")
    """))

    # 6. 线程并发测试
    print("\n6. 线程并发 get_stock_list_in_sector")
    run_test("4线程并发", textwrap.dedent("""\
        from xtquant import xtdata
        from concurrent.futures import ThreadPoolExecutor
        sectors = ['沪深A股', '沪深ETF', '上证指数', '深证指数']
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(xtdata.get_stock_list_in_sector, sectors))
        for s, r in zip(sectors, results):
            print(f"  {s}: {len(r)}")
    """))

    # 7. get_client 方法测试
    print("\n7. get_client().get_connect_status()")
    run_test("get_client", textwrap.dedent("""\
        from xtquant import xtdata
        client = xtdata.get_client()
        print(f"connected={client.get_connect_status()}")
    """))

    # 8. download 相关（不读本地数据）
    print("\n8. download_sector_data (不读本地缓存)")
    run_test("download_sector_data", textwrap.dedent("""\
        from xtquant import xtdata
        xtdata.download_sector_data()
        print("ok")
    """))

    print("\n=== 诊断完成 ===")


if __name__ == "__main__":
    main()

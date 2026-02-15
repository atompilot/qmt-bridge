"""定位 xtdata BSON 崩溃的根因文件。

第二轮排查：上一轮发现移除 datadir 下的单个文件/目录无法修复崩溃。
本轮测试：
1. 整个 datadir 目录重命名 → 确认是否在 datadir 中
2. 若 datadir 不是原因，测试 userdata_mini 下的共享内存文件
3. 若整个 datadir 是原因，用组合排除法找出具体子目录
"""

import os
import subprocess
import sys

USERDATA = (
    r"C:\Users\wangtong\Documents\Softwares"
    r"\迅投极速策略交易系统交易终端 华泰证券QMT实盘"
    r"\userdata_mini"
)
DATADIR = os.path.join(USERDATA, "datadir")


def test_get_local_data() -> tuple[bool, str]:
    """在子进程中测试 get_local_data，返回 (是否成功, 输出信息)。"""
    code = (
        "from xtquant import xtdata; xtdata.enable_hello = False; "
        "d = xtdata.get_local_data(field_list=[], stock_list=['000001.SZ'], "
        "period='1d', start_time='', end_time='', count=1); "
        "print(f'OK rows={len(d)}')"
    )
    try:
        r = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True, text=True, timeout=15,
        )
        if r.returncode == 0:
            return True, r.stdout.strip()
        err_lines = r.stderr.strip().splitlines()[-2:]
        return False, f"exit={r.returncode} | {' '.join(l.strip() for l in err_lines)}"
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT"


def test_get_market_data_ex() -> tuple[bool, str]:
    """测试 get_market_data_ex。"""
    code = (
        "from xtquant import xtdata; xtdata.enable_hello = False; "
        "d = xtdata.get_market_data_ex(field_list=[], stock_list=['000001.SZ'], "
        "period='1d', start_time='', end_time='', count=1); "
        "print(f'OK rows={len(d)}')"
    )
    try:
        r = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True, text=True, timeout=15,
        )
        if r.returncode == 0:
            return True, r.stdout.strip()
        err_lines = r.stderr.strip().splitlines()[-2:]
        return False, f"exit={r.returncode} | {' '.join(l.strip() for l in err_lines)}"
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT"


def safe_rename(src: str, dst: str) -> bool:
    """安全重命名，返回是否成功。"""
    try:
        os.rename(src, dst)
        return True
    except OSError as e:
        print(f"   无法重命名 {src}: {e}")
        return False


def test_removing(label: str, path: str) -> bool | None:
    """临时移除 path，测试 get_local_data，立即恢复。返回移除后是否修复（None=无法测试）。"""
    bak = path + ".bak_test"
    if not os.path.exists(path):
        print(f"   {label}: 不存在，跳过")
        return None

    print(f"   测试移除: {label}")
    if not safe_rename(path, bak):
        return None

    ok, msg = test_get_local_data()
    print(f"     get_local_data: {'OK' if ok else 'CRASH'} — {msg}")

    if not safe_rename(bak, path):
        print(f"   ⚠ 恢复失败！请手动: rename {bak} -> {path}")
    return ok


def main():
    print("=== xtdata BSON 崩溃根因排查（第二轮）===\n")

    # 0. 确认基线
    print("0. 基线确认")
    ok, msg = test_get_local_data()
    print(f"   get_local_data: {'OK' if ok else 'CRASH'} — {msg}")
    if ok:
        print("   当前状态正常，无需排查！")
        return
    print()

    # 1. 测试整个 datadir 重命名
    print("1. 测试移除整个 datadir 目录")
    fixed = test_removing("datadir (整个目录)", DATADIR)
    if fixed:
        print("   >>> 移除整个 datadir 后恢复正常！问题在 datadir 内部 <<<")
        print()
        # 进一步用组合排除法定位
        print("2. 组合排除定位 datadir 内的具体子项")
        # 获取 datadir 下所有子项
        items = sorted(os.listdir(DATADIR))
        print(f"   datadir 内容: {items}")

        # 逐个保留策略：每次只保留一个子项，其余全移除
        # 如果只保留某个子项时崩溃，说明该子项是问题源
        for item in items:
            item_path = os.path.join(DATADIR, item)
            other_items = [x for x in items if x != item]

            # 移除其他所有项
            bak_paths = []
            all_renamed = True
            for other in other_items:
                other_path = os.path.join(DATADIR, other)
                other_bak = other_path + ".bak_test"
                if os.path.exists(other_path):
                    if not safe_rename(other_path, other_bak):
                        all_renamed = False
                        break
                    bak_paths.append((other_bak, other_path))

            if not all_renamed:
                # 恢复已移除的
                for bak, orig in bak_paths:
                    safe_rename(bak, orig)
                print(f"   {item}: 无法完成测试")
                continue

            # 测试：只剩 item 时是否崩溃
            ok, msg = test_get_local_data()
            status = "CRASH" if not ok else "OK"
            print(f"   只保留 {item}: {status}")

            # 恢复所有
            for bak, orig in bak_paths:
                safe_rename(bak, orig)

            if not ok:
                print(f"   >>> {item} 单独存在就会导致崩溃！<<<")
        return

    if fixed is False:
        print("   移除整个 datadir 后仍然崩溃！问题不在 datadir")
        print()

    # 2. 测试 userdata_mini 下的共享内存文件
    print("2. 测试 userdata_mini 下的共享内存/IPC 文件")
    shm_files = [
        "miniqmtShmQuoteCache",
        "miniqmtShmTradeDateListCache",
        "miniqmtShmStrategyCache",
    ]
    for f in shm_files:
        fixed = test_removing(f, os.path.join(USERDATA, f))
        if fixed:
            print(f"   >>> {f} 是问题源！<<<")

    # 3. 测试各市场的 StockListCache
    print("\n3. 测试 miniqmtShmStockListCache* 文件")
    for f in sorted(os.listdir(USERDATA)):
        if f.startswith("miniqmtShmStockListCache"):
            fixed = test_removing(f, os.path.join(USERDATA, f))
            if fixed:
                print(f"   >>> {f} 是问题源！<<<")

    # 4. 测试 down_queue 文件（残留的 IPC 队列）
    print("\n4. 测试 down_queue_win_* 文件（残留 IPC 队列）")
    dq_files = [f for f in os.listdir(USERDATA)
                if f.startswith("down_queue_win_") and not f.endswith("__mutex")]
    print(f"   共 {len(dq_files)} 个 down_queue 文件")
    # 测试移除所有 down_queue 文件（包括 mutex 和 lock）
    bak_paths = []
    all_ok = True
    for f in os.listdir(USERDATA):
        if f.startswith(("down_queue_win_", "lock_down_queue_win_")):
            fp = os.path.join(USERDATA, f)
            bp = fp + ".bak_test"
            if os.path.exists(fp) and os.path.isfile(fp):
                if safe_rename(fp, bp):
                    bak_paths.append((bp, fp))
                else:
                    all_ok = False

    if all_ok and bak_paths:
        ok, msg = test_get_local_data()
        print(f"   移除所有 down_queue_win_*: {'OK' if ok else 'CRASH'} — {msg}")
        if ok:
            print("   >>> down_queue 残留文件是问题源！<<<")
    else:
        print("   无法完成测试")

    # 恢复
    for bak, orig in bak_paths:
        safe_rename(bak, orig)

    # 5. 测试 up_queue 文件
    print("\n5. 测试 up_queue_* 文件")
    bak_paths = []
    for f in os.listdir(USERDATA):
        if f.startswith(("up_queue_", "lock_up_queue_")):
            fp = os.path.join(USERDATA, f)
            bp = fp + ".bak_test"
            if os.path.exists(fp) and os.path.isfile(fp):
                if safe_rename(fp, bp):
                    bak_paths.append((bp, fp))

    if bak_paths:
        ok, msg = test_get_local_data()
        print(f"   移除所有 up_queue_*: {'OK' if ok else 'CRASH'} — {msg}")
        if ok:
            print("   >>> up_queue 文件是问题源！<<<")
    for bak, orig in bak_paths:
        safe_rename(bak, orig)

    # 6. 测试 quoter 目录
    print("\n6. 测试 quoter 目录")
    test_removing("quoter", os.path.join(USERDATA, "quoter"))

    print("\n=== 排查完成 ===")


if __name__ == "__main__":
    main()

# CLAUDE.md — 开发准则

本文件供 Claude Code 参考，确保代码风格和工作流与项目保持一致。

## 项目概览

QMT Bridge：将 miniQMT (xtquant) 的行情与交易能力通过 HTTP/WebSocket 暴露给局域网设备。

- **语言**: Python 3.10+
- **构建**: hatchling (pyproject.toml)
- **服务端**: FastAPI + uvicorn，运行在 Windows (xtquant 依赖 QMT 客户端)
- **客户端**: 零依赖 (stdlib)，跨平台

## 目录结构

```
src/qmt_bridge/
  server/          # FastAPI 服务端 (routers/, ws/, trading/)
  client/          # Python 客户端 (Mixin 模式)
  _version.py      # 单一版本源
scripts/           # 独立脚本 (download_all.py 等)
tests/             # pytest 测试
dashboard/         # Streamlit 仪表盘
logs/              # 运行日志 (gitignored)
.trash/            # 废弃代码暂存 (gitignored)
```

## 常用命令

```bash
just install-all          # 安装全部依赖
just serve                # 启动 API 服务
just download-all         # 下载 A 股历史行情 + 财务数据
just test                 # 运行测试
just check                # 格式化 + lint (ruff)
just build                # 构建 wheel
```

## 开发规范

### 代码风格

- 中文注释和 docstring，保持与现有代码一致
- commit message 格式: `type: 中文描述 (vX.Y.Z)`，type 使用 `feat` / `fix` / `refactor` / `chore`
- 日志使用 `logging` 模块，避免 print 调试输出残留

### 废弃代码处理

- **不直接删除**，移入 `.trash/` 目录保留备查
- 文件名添加时间戳后缀，避免重名冲突: `filename.YYYYMMDD_HHMMSS.py`
- `.trash/` 已在 `.gitignore` 中，不会进入版本控制
- 示例: `mv scripts/old_script.py .trash/old_script.20260213_143000.py`

### 文件管理

- 优先编辑现有文件，避免不必要的新建文件
- 独立脚本放 `scripts/`，保持可单独运行（不 import 项目内部模块的非公开 API）
- 新增 `scripts/` 脚本时同步更新 `justfile` 中的快捷命令

### 依赖管理

- 客户端 (`client/`) 保持零依赖 (stdlib only)
- 服务端依赖声明在 `pyproject.toml` 的 `[project.optional-dependencies]`
- 脚本依赖归入 `scripts` extra

### 版本号

- 单一版本源: `src/qmt_bridge/_version.py`
- hatch 自动读取，发布前手动更新

## 已知问题与排障手册

### BSON 断言崩溃 (`Assertion failed: u < 1000000, bsonobj.cpp`)

**现象**：调用 `xtdata.get_local_data()` 或 `xtdata.get_market_data_ex()` 时进程崩溃，
错误信息为 `Assertion failed: u < 1000000, file ...\bsonobj.cpp, line 1388`。
`get_full_tick()`、`get_stock_list_in_sector()` 等其他接口正常。

**根因**：QMT 服务端进程（XtMiniQmt.exe / miniquote.exe）内部状态损坏，
返回了无效的 BSON 响应。与磁盘数据文件无关（经排查：移除整个 datadir 仍崩溃）。

**解决方法**：**重启 QMT 客户端软件**即可恢复。

**排查记录（2026-02-15）**：
1. 最初误判为线程并发问题，添加了 `asyncio.Lock` 串行化依赖（保留，有防护价值）
2. 将定时下载调度器拆分为独立进程 `qmt-scheduler`（保留，架构更合理）
3. 经诊断脚本 `scripts/diagnose_bson.py` 确认只有 `get_local_data` / `get_market_data_ex` 崩溃
4. 经 `scripts/find_bad_cache.py` 排除了所有磁盘文件（datadir、共享内存、IPC 队列）
5. 最终确认重启 QMT 后问题消失，属于 QMT 服务端内存状态损坏

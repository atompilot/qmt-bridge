"""服务端配置管理模块 ── 环境变量与 .env 文件加载。

本模块负责：
1. 从 .env 文件加载配置到 os.environ（纯标准库实现，不依赖 python-dotenv）
2. 定义 Settings 数据类，包含所有可配置项
3. 提供全局配置单例的获取/重置接口

配置优先级（从高到低）：
    命令行参数 > 系统环境变量 > .env 文件

所有环境变量均以 ``QMT_BRIDGE_`` 前缀命名，例如：
    - QMT_BRIDGE_HOST: 监听地址
    - QMT_BRIDGE_PORT: 监听端口
    - QMT_BRIDGE_API_KEY: API 认证密钥
    - QMT_BRIDGE_TRADING_ENABLED: 是否启用交易模块
"""

import os
from dataclasses import dataclass, field
from pathlib import Path


def _load_env_file(env_path: Path | None = None) -> None:
    """从 .env 文件加载键值对到 os.environ 中。

    使用纯标准库实现，不依赖 python-dotenv 第三方包。
    已存在于系统环境中的变量不会被 .env 文件中的同名配置覆盖，
    确保系统环境变量的优先级高于 .env 文件。

    Args:
        env_path: .env 文件路径。若为 None，则在当前工作目录下查找 .env 文件。
    """
    if env_path is None:
        # 默认在当前工作目录下查找 .env 文件
        env_path = Path.cwd() / ".env"
    if not env_path.is_file():
        return
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # 跳过空行和注释行
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, val = line.partition("=")
                key, val = key.strip(), val.strip()
                # 系统环境变量优先：已存在的变量不覆盖
                if key and key not in os.environ:
                    os.environ[key] = val


@dataclass
class Settings:
    """应用配置数据类，所有可配置项集中管理。

    配置项分为以下几组：
    - 服务器基础配置（host/port/log_level/workers）
    - 安全认证配置（api_key/require_auth_for_data）
    - 交易模块配置（trading_enabled/mini_qmt_path/trading_account_id）
    - 通知模块配置（notify_enabled/notify_backends 等）
    - 飞书 Webhook 配置
    - 通用 Webhook 配置
    """

    # ---- 服务器基础配置 ----
    host: str = "0.0.0.0"       # 监听地址，默认监听所有网卡
    port: int = 8000             # 监听端口
    log_level: str = "info"      # 日志级别（传递给 uvicorn）
    workers: int = 1             # 工作进程数（Windows 下建议为 1）

    # ---- 安全认证配置 ----
    api_key: str = ""                    # API 密钥（为空表示未配置认证）
    require_auth_for_data: bool = False  # 是否对数据查询接口也要求认证

    # ---- 交易模块配置（底层使用 xtquant.xttrader）----
    trading_enabled: bool = False   # 是否启用交易模块
    mini_qmt_path: str = ""        # miniQMT 客户端安装路径
    trading_account_id: str = ""   # 交易资金账号 ID

    # ---- 通知模块配置 ----
    notify_enabled: bool = False   # 是否启用通知推送
    notify_backends: str = ""      # 通知后端，逗号分隔，如 "feishu", "webhook", "feishu,webhook"
    notify_event_types: str = ""   # 允许推送的事件类型（逗号分隔），为空表示全部允许
    notify_ignore_event_types: str = ""  # 排除的事件类型（逗号分隔）

    # ---- 飞书 Webhook 配置 ----
    feishu_webhook_url: str = ""     # 飞书机器人 Webhook 地址
    feishu_webhook_secret: str = ""  # 飞书 Webhook v2 签名密钥（可选）

    # ---- 通用 Webhook 配置 ----
    webhook_url: str = ""       # 通用 Webhook 回调地址
    webhook_secret: str = ""    # Webhook 密钥（通过 X-Webhook-Secret 请求头发送）

    # ---- 定时下载调度配置 ----
    scheduler_kline_enabled: bool = True         # 是否启用 K 线增量下载
    scheduler_kline_periods: str = "1d,5m,1m"    # K 线周期，逗号分隔
    scheduler_kline_sectors: str = "沪深A股,沪深ETF,沪深指数"  # K 线下载板块
    scheduler_financial_enabled: bool = True      # 是否启用财务数据增量下载
    scheduler_financial_sectors: str = "沪深A股"  # 财务数据只对 A 股有意义

    @classmethod
    def from_env(cls, env_path: Path | None = None) -> "Settings":
        """从环境变量创建 Settings 实例。

        会先调用 _load_env_file() 加载 .env 文件，
        然后从 os.environ 中读取所有 ``QMT_BRIDGE_*`` 配置项。

        Args:
            env_path: .env 文件路径。若为 None 则使用默认路径。

        Returns:
            根据环境变量构建的 Settings 实例。
        """
        _load_env_file(env_path)
        return cls(
            host=os.environ.get("QMT_BRIDGE_HOST", "0.0.0.0"),
            port=int(os.environ.get("QMT_BRIDGE_PORT", "8000")),
            log_level=os.environ.get("QMT_BRIDGE_LOG_LEVEL", "info"),
            workers=int(os.environ.get("QMT_BRIDGE_WORKERS", "1")),
            api_key=os.environ.get("QMT_BRIDGE_API_KEY", ""),
            require_auth_for_data=os.environ.get(
                "QMT_BRIDGE_REQUIRE_AUTH_FOR_DATA", ""
            ).lower()
            in ("1", "true", "yes"),
            trading_enabled=os.environ.get(
                "QMT_BRIDGE_TRADING_ENABLED", ""
            ).lower()
            in ("1", "true", "yes"),
            mini_qmt_path=os.environ.get("QMT_BRIDGE_MINI_QMT_PATH", ""),
            trading_account_id=os.environ.get(
                "QMT_BRIDGE_TRADING_ACCOUNT_ID", ""
            ),
            # 通知相关配置
            notify_enabled=os.environ.get(
                "QMT_BRIDGE_NOTIFY_ENABLED", ""
            ).lower()
            in ("1", "true", "yes"),
            notify_backends=os.environ.get("QMT_BRIDGE_NOTIFY_BACKENDS", ""),
            notify_event_types=os.environ.get(
                "QMT_BRIDGE_NOTIFY_EVENT_TYPES", ""
            ),
            notify_ignore_event_types=os.environ.get(
                "QMT_BRIDGE_NOTIFY_IGNORE_EVENT_TYPES", ""
            ),
            feishu_webhook_url=os.environ.get(
                "QMT_BRIDGE_FEISHU_WEBHOOK_URL", ""
            ),
            feishu_webhook_secret=os.environ.get(
                "QMT_BRIDGE_FEISHU_WEBHOOK_SECRET", ""
            ),
            webhook_url=os.environ.get("QMT_BRIDGE_WEBHOOK_URL", ""),
            webhook_secret=os.environ.get("QMT_BRIDGE_WEBHOOK_SECRET", ""),
            # 定时下载调度配置
            scheduler_kline_enabled=os.environ.get(
                "QMT_BRIDGE_SCHEDULER_KLINE_ENABLED", "true"
            ).lower()
            in ("1", "true", "yes"),
            scheduler_kline_periods=os.environ.get(
                "QMT_BRIDGE_SCHEDULER_KLINE_PERIODS", "1d,5m,1m"
            ),
            scheduler_kline_sectors=os.environ.get(
                "QMT_BRIDGE_SCHEDULER_KLINE_SECTORS", "沪深A股,沪深ETF,沪深指数"
            ),
            scheduler_financial_enabled=os.environ.get(
                "QMT_BRIDGE_SCHEDULER_FINANCIAL_ENABLED", "true"
            ).lower()
            in ("1", "true", "yes"),
            scheduler_financial_sectors=os.environ.get(
                "QMT_BRIDGE_SCHEDULER_FINANCIAL_SECTORS", "沪深A股"
            ),
        )


# 模块级全局配置单例，延迟初始化（首次调用 get_settings() 时创建）
_settings: Settings | None = None


def get_settings() -> Settings:
    """获取全局配置单例。

    若单例尚未初始化，则调用 Settings.from_env() 从环境变量创建。
    该函数也被 FastAPI 依赖注入系统使用（Depends(get_settings)）。

    Returns:
        全局唯一的 Settings 实例。
    """
    global _settings
    if _settings is None:
        _settings = Settings.from_env()
    return _settings


def reset_settings(settings: Settings | None = None) -> None:
    """替换全局配置单例。

    主要在 CLI 入口（cli.py）中使用，用命令行参数覆盖默认配置。

    Args:
        settings: 新的配置对象。若为 None 则清空单例（下次 get_settings 时重新创建）。
    """
    global _settings
    _settings = settings

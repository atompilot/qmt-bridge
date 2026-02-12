"""API Key 认证模块。

本模块实现基于 HTTP 请求头 ``X-API-Key`` 的 API 密钥认证机制，
提供两种认证级别的 FastAPI 依赖函数：

1. ``require_api_key`` —— 强制认证（用于交易等敏感接口）
2. ``optional_api_key`` —— 可选认证（用于数据查询接口，可通过配置开关控制）

认证流程：
    客户端在 HTTP 请求头中携带 ``X-API-Key: <your-api-key>``，
    服务端将其与配置中的 ``api_key`` 进行恒定时间比较（防止时序攻击）。

使用示例::

    @router.post("/order")
    async def place_order(
        _api_key: str = Depends(require_api_key),
    ):
        ...  # 已通过认证
"""

import hmac

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from .config import Settings, get_settings

# 定义 API Key 请求头提取器，从 HTTP 头 "X-API-Key" 中读取密钥
# auto_error=False 表示缺少该头时不自动抛错，由我们手动处理
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(
    api_key: str | None = Security(_api_key_header),
    settings: Settings = Depends(get_settings),
) -> str:
    """强制 API Key 认证依赖（用于交易等敏感接口）。

    该依赖函数在以下情况抛出异常：
    - 服务端未配置 API Key（settings.api_key 为空）：返回 503
    - 客户端未提供 API Key 或密钥不匹配：返回 401

    密钥比较使用 hmac.compare_digest() 进行恒定时间比较，
    防止基于响应时间差异的时序攻击（timing attack）。

    Args:
        api_key: 从请求头 ``X-API-Key`` 中提取的密钥值（由 FastAPI Security 自动注入）。
        settings: 全局配置对象（由 FastAPI Depends 自动注入）。

    Returns:
        验证通过的 API Key 字符串。

    Raises:
        HTTPException: 503 —— 服务端未配置 API Key。
        HTTPException: 401 —— 客户端密钥无效或缺失。
    """
    if not settings.api_key:
        # 服务端未配置 API Key，无法进行认证
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API key not configured on server",
        )
    if api_key is None or not hmac.compare_digest(api_key, settings.api_key):
        # 客户端未提供密钥，或密钥不匹配
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return api_key


def optional_api_key(
    api_key: str | None = Security(_api_key_header),
    settings: Settings = Depends(get_settings),
) -> str | None:
    """可选 API Key 认证依赖（用于数据查询接口）。

    行为由配置项 ``require_auth_for_data`` 控制：
    - 若为 False（默认）：不要求认证，直接放行，返回客户端提供的 key（可能为 None）
    - 若为 True：委托给 require_api_key() 执行强制认证

    这使得数据查询接口默认无需认证即可访问，
    但管理员可通过环境变量 ``QMT_BRIDGE_REQUIRE_AUTH_FOR_DATA=true``
    为数据接口也启用认证保护。

    Args:
        api_key: 从请求头 ``X-API-Key`` 中提取的密钥值。
        settings: 全局配置对象。

    Returns:
        验证通过的 API Key 字符串，或 None（未要求认证时）。
    """
    if not settings.require_auth_for_data:
        # 数据接口不要求认证，直接放行
        return api_key
    # 委托给强制认证函数处理
    return require_api_key(api_key, settings)

"""xtdata 请求级串行化模块。

xtquant 的 C 扩展不是线程安全的。FastAPI 的同步路由处理函数在线程池中
并发执行，多个请求同时调用 xtdata.* 会导致内部 BSON 序列化出现数据竞争，
触发 ``Assertion failed: u < 1000000`` 崩溃。

本模块通过 HTTP 中间件 + asyncio.Lock 实现请求级串行化：
- 同一时刻只允许一个 HTTP 请求进入路由处理函数
- 不修改 xtdata 模块本身，避免内部互调死锁风险
- 后台调度器的基础下载任务也通过同一把锁串行化

asyncio.Lock 在事件循环层面工作，持锁期间线程池中的 xtdata 调用正常执行，
释锁后下一个请求才进入处理函数，从而保证 xtdata 不被并发调用。

使用纯 ASGI 中间件（而非 BaseHTTPMiddleware），在服务关闭时排队请求
能立即取消退出，不会产生大量 CancelledError。
"""

import asyncio
import logging

logger = logging.getLogger("qmt_bridge")

# 全局异步锁，确保同一时刻只有一个请求/任务调用 xtdata
xtdata_lock = asyncio.Lock()


class XtdataSerializerMiddleware:
    """纯 ASGI 中间件：串行化所有 HTTP 请求，防止并发调用 xtdata。

    通过 asyncio.Lock 保证同一时刻只有一个请求的同步处理函数在线程池中执行。
    WebSocket 连接不受此中间件影响（仅拦截 HTTP 请求）。
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        # 只对 /api/ 路径加锁，/docs /openapi.json 等静态端点不受影响
        path = scope.get("path", "")
        if path.startswith("/api/"):
            async with xtdata_lock:
                await self.app(scope, receive, send)
        else:
            await self.app(scope, receive, send)

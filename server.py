"""QMT Bridge — FastAPI server exposing xtquant market data over HTTP/WebSocket."""

import argparse
import asyncio
import json
import os
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import uvicorn
from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from xtquant import xtdata

from helpers import _market_data_to_records, _numpy_to_python
from models import DownloadRequest
from routers import (
    calendar,
    download,
    etf,
    financial,
    futures,
    instrument,
    market,
    meta,
    option,
    sector,
    tick,
)

# ---------------------------------------------------------------------------
# Load .env file (stdlib only, no python-dotenv dependency)
# ---------------------------------------------------------------------------

_env_path = Path(__file__).resolve().parent / ".env"
if _env_path.is_file():
    with open(_env_path, encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if not _line or _line.startswith("#"):
                continue
            if "=" in _line:
                _key, _, _val = _line.partition("=")
                _key, _val = _key.strip(), _val.strip()
                # Only set if not already defined (real env vars take precedence)
                if _key and _key not in os.environ:
                    os.environ[_key] = _val

app = FastAPI(title="QMT Bridge", description="miniQMT market data API bridge")

# ---------------------------------------------------------------------------
# Register new routers
# ---------------------------------------------------------------------------

app.include_router(market.router)
app.include_router(tick.router)
app.include_router(sector.router)
app.include_router(calendar.router)
app.include_router(financial.router)
app.include_router(instrument.router)
app.include_router(option.router)
app.include_router(etf.etf_router)
app.include_router(etf.cb_router)
app.include_router(futures.router)
app.include_router(meta.router)
app.include_router(download.router)


# ---------------------------------------------------------------------------
# Legacy REST endpoints (kept for backward compatibility)
# ---------------------------------------------------------------------------

@app.get("/api/history", tags=["legacy"])
def get_history(
    stock: str = Query(..., description="股票代码，如 000001.SZ"),
    period: str = Query("1d", description="K线周期: tick/1m/5m/15m/30m/60m/1d"),
    count: int = Query(100, description="返回条数"),
    fields: str = Query(
        "open,high,low,close,volume",
        description="字段列表，逗号分隔",
    ),
):
    field_list = [f.strip() for f in fields.split(",")]
    raw = xtdata.get_market_data(
        field_list=field_list,
        stock_list=[stock],
        period=period,
        count=count,
    )
    records = _market_data_to_records(raw, [stock], field_list)
    return {"stock": stock, "period": period, "count": count, "data": records.get(stock, [])}


@app.get("/api/batch_history", tags=["legacy"])
def get_batch_history(
    stocks: str = Query(..., description="股票代码列表，逗号分隔"),
    period: str = Query("1d", description="K线周期"),
    count: int = Query(100, description="返回条数"),
    fields: str = Query(
        "open,high,low,close,volume",
        description="字段列表，逗号分隔",
    ),
):
    stock_list = [s.strip() for s in stocks.split(",")]
    field_list = [f.strip() for f in fields.split(",")]
    raw = xtdata.get_market_data(
        field_list=field_list,
        stock_list=stock_list,
        period=period,
        count=count,
    )
    records = _market_data_to_records(raw, stock_list, field_list)
    return {"stocks": stock_list, "period": period, "count": count, "data": records}


@app.get("/api/full_tick", tags=["legacy"])
def get_full_tick(
    stocks: str = Query(..., description="股票代码列表，逗号分隔"),
):
    stock_list = [s.strip() for s in stocks.split(",")]
    raw = xtdata.get_full_tick(code_list=stock_list)
    return {"data": _numpy_to_python(raw)}


@app.get("/api/sector_stocks", tags=["legacy"])
def get_sector_stocks(
    sector: str = Query(..., description="板块名称，如 沪深A股"),
):
    stock_list = xtdata.get_stock_list_in_sector(sector)
    return {"sector": sector, "stocks": stock_list}


@app.get("/api/instrument_detail", tags=["legacy"])
def get_instrument_detail(
    stock: str = Query(..., description="股票代码，如 000001.SZ"),
):
    detail = xtdata.get_instrument_detail(stock)
    return {"stock": stock, "detail": _numpy_to_python(detail)}


@app.post("/api/download", tags=["legacy"])
def download_data(req: DownloadRequest):
    xtdata.download_history_data(
        req.stock, period=req.period, start_time=req.start, end_time=req.end
    )
    return {"status": "ok", "stock": req.stock, "period": req.period}


# ---------------------------------------------------------------------------
# WebSocket endpoint — realtime quotes
# ---------------------------------------------------------------------------

@app.websocket("/ws/realtime")
async def ws_realtime(ws: WebSocket):
    await ws.accept()
    seq_ids: list[int] = []
    loop = asyncio.get_event_loop()

    try:
        # Wait for subscription request
        msg = await ws.receive_text()
        payload = json.loads(msg)
        stocks: list[str] = payload.get("stocks", [])
        period: str = payload.get("period", "tick")

        async def _send(data):
            try:
                await ws.send_json(data)
            except Exception:
                pass

        def on_data(data):
            """Callback invoked by xtdata in its own thread."""
            clean = _numpy_to_python(data)
            asyncio.run_coroutine_threadsafe(_send(clean), loop)

        # Subscribe each stock
        for stock in stocks:
            seq = xtdata.subscribe_quote(
                stock_code=stock,
                period=period,
                callback=on_data,
            )
            seq_ids.append(seq)

        # Keep connection alive until client disconnects
        while True:
            await ws.receive_text()

    except WebSocketDisconnect:
        pass
    finally:
        for seq in seq_ids:
            xtdata.unsubscribe_quote(seq)


# ---------------------------------------------------------------------------
# WebSocket endpoint — whole market quote subscription
# ---------------------------------------------------------------------------

@app.websocket("/ws/whole_quote")
async def ws_whole_quote(ws: WebSocket):
    await ws.accept()
    seq_id = None
    loop = asyncio.get_event_loop()

    try:
        msg = await ws.receive_text()
        payload = json.loads(msg)
        code_list: list[str] = payload.get("codes", [])

        async def _send(data):
            try:
                await ws.send_json(data)
            except Exception:
                pass

        def on_data(data):
            clean = _numpy_to_python(data)
            asyncio.run_coroutine_threadsafe(_send(clean), loop)

        seq_id = xtdata.subscribe_whole_quote(code_list, callback=on_data)

        while True:
            await ws.receive_text()

    except WebSocketDisconnect:
        pass
    finally:
        if seq_id is not None:
            xtdata.unsubscribe_quote(seq_id)


# ---------------------------------------------------------------------------
# WebSocket endpoint — download progress
# ---------------------------------------------------------------------------

@app.websocket("/ws/download_progress")
async def ws_download_progress(ws: WebSocket):
    await ws.accept()
    loop = asyncio.get_event_loop()

    try:
        msg = await ws.receive_text()
        payload = json.loads(msg)
        stocks: list[str] = payload.get("stocks", [])
        period: str = payload.get("period", "1d")
        start_time: str = payload.get("start_time", "")
        end_time: str = payload.get("end_time", "")

        async def _send(data):
            try:
                await ws.send_json(data)
            except Exception:
                pass

        def on_progress(data):
            clean = _numpy_to_python(data)
            asyncio.run_coroutine_threadsafe(_send(clean), loop)

        xtdata.download_history_data2(
            stocks,
            period=period,
            start_time=start_time,
            end_time=end_time,
            callback=on_progress,
        )

        await ws.send_json({"status": "done"})

    except WebSocketDisconnect:
        pass


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="QMT Bridge API Server")
    parser.add_argument(
        "--host",
        default=os.environ.get("QMT_BRIDGE_HOST", "0.0.0.0"),
        help="Listen host (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("QMT_BRIDGE_PORT", "8000")),
        help="Listen port (default: 8000)",
    )
    args = parser.parse_args()
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level=os.environ.get("QMT_BRIDGE_LOG_LEVEL", "info"),
        workers=int(os.environ.get("QMT_BRIDGE_WORKERS", "1")),
    )


if __name__ == "__main__":
    main()

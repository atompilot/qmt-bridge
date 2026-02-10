"""CLI entry point — ``qmt-server`` command."""

import argparse
import os

from .config import Settings, _load_env_file, reset_settings


def main():
    """Parse CLI args, build settings, and start the server."""
    # Load .env before parsing so defaults come from env
    _load_env_file()

    parser = argparse.ArgumentParser(
        prog="qmt-server",
        description="QMT Bridge API Server",
    )
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
    parser.add_argument(
        "--log-level",
        default=os.environ.get("QMT_BRIDGE_LOG_LEVEL", "info"),
        choices=["critical", "error", "warning", "info", "debug"],
        help="Uvicorn log level (default: info)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=int(os.environ.get("QMT_BRIDGE_WORKERS", "1")),
        help="Number of workers (default: 1, keep 1 on Windows)",
    )
    parser.add_argument(
        "--trading",
        action="store_true",
        default=os.environ.get("QMT_BRIDGE_TRADING_ENABLED", "").lower()
        in ("1", "true", "yes"),
        help="Enable trading module",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("QMT_BRIDGE_API_KEY", ""),
        help="API key for authenticated endpoints",
    )
    parser.add_argument(
        "--mini-qmt-path",
        default=os.environ.get("QMT_BRIDGE_MINI_QMT_PATH", ""),
        help="Path to miniQMT installation (for trading)",
    )
    parser.add_argument(
        "--account-id",
        default=os.environ.get("QMT_BRIDGE_TRADING_ACCOUNT_ID", ""),
        help="Trading account ID",
    )

    args = parser.parse_args()

    # Build settings from CLI args (override env)
    settings = Settings(
        host=args.host,
        port=args.port,
        log_level=args.log_level,
        workers=args.workers,
        api_key=args.api_key,
        trading_enabled=args.trading,
        mini_qmt_path=args.mini_qmt_path,
        trading_account_id=args.account_id,
    )
    reset_settings(settings)

    import uvicorn

    from .app import create_app

    app = create_app(settings)
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level,
        workers=settings.workers,
    )


if __name__ == "__main__":
    main()

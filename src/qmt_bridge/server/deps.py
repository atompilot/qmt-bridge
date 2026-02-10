"""FastAPI dependency injection helpers."""

from fastapi import Depends, HTTPException, Request, status

from .config import Settings, get_settings


def get_trader_manager(request: Request):
    """Retrieve the XtTraderManager from app.state (set during lifespan)."""
    manager = getattr(request.app.state, "trader_manager", None)
    if manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Trading module is not enabled",
        )
    return manager

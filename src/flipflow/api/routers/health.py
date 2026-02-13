"""Health check endpoint with database connectivity."""

import logging

from fastapi import APIRouter, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health")
async def health(request: Request):
    db_ok = False
    try:
        engine = request.app.state.engine
        factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with factory() as session:
            await session.execute(text("SELECT 1"))
            db_ok = True
    except Exception as e:
        logger.warning("Health check DB probe failed: %s", e)

    status = "ok" if db_ok else "degraded"
    return {
        "status": status,
        "service": "flipflow",
        "version": "0.1.0",
        "database": "connected" if db_ok else "unreachable",
    }

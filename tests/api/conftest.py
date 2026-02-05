"""Shared fixtures for API tests."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine

from flipflow.api.app import create_app
from flipflow.core.config import FlipFlowConfig
from flipflow.core.models.base import Base
import flipflow.core.models  # noqa: F401


@pytest.fixture
async def app():
    config = FlipFlowConfig(
        database_url="sqlite+aiosqlite:///:memory:",
        ebay_mode="mock",
        _env_file=None,
    )
    application = create_app(config)

    # Manually set up engine (lifespan doesn't run with ASGITransport)
    engine = create_async_engine(
        config.database_url,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    application.state.engine = engine

    yield application

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def client(app):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as c:
        yield c

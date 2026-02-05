"""Shared test fixtures for FlipFlow."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from flipflow.core.config import FlipFlowConfig
from flipflow.core.models import Base  # noqa: F401 — importing triggers all model registration
import flipflow.core.models  # noqa: F401 — ensure all models are loaded for metadata.create_all
from flipflow.infrastructure.ebay_mock.mock_client import MockEbayClient


@pytest.fixture
def test_config() -> FlipFlowConfig:
    """Config with test-appropriate defaults."""
    return FlipFlowConfig(
        database_url="sqlite+aiosqlite:///:memory:",
        ebay_mode="mock",
        resurrection_delay_seconds=0,  # No waiting in tests
    )


@pytest.fixture
async def db_engine(test_config):
    """Async engine with in-memory SQLite."""
    engine = create_async_engine(
        test_config.database_url,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine) -> AsyncSession:
    """Async session for testing."""
    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest.fixture
def mock_ebay() -> MockEbayClient:
    """Mock eBay client pre-loaded with fixture data."""
    return MockEbayClient(load_fixtures=True)


@pytest.fixture
def empty_mock_ebay() -> MockEbayClient:
    """Mock eBay client with no fixture data."""
    return MockEbayClient(load_fixtures=False)

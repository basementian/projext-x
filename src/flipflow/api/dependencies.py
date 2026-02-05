"""FastAPI dependency injection — provides DB sessions, services, and gateways."""

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from flipflow.core.config import FlipFlowConfig
from flipflow.infrastructure.ebay_mock.mock_client import MockEbayClient


async def get_config(request: Request) -> FlipFlowConfig:
    return request.app.state.config


async def get_db(request: Request) -> AsyncSession:
    engine = request.app.state.engine
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_ebay(request: Request):
    config = request.app.state.config
    if config.ebay_mode == "mock":
        return MockEbayClient(load_fixtures=True)
    # Future: return RealEbayClient(config)
    return MockEbayClient(load_fixtures=True)

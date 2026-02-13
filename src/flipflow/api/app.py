"""FastAPI application factory."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from flipflow.api.routers import health, listings, offers, queue, relister, repricer, zombies
from flipflow.core.config import FlipFlowConfig
from flipflow.core.logging_config import setup_logging
from flipflow.core.models.base import Base
from flipflow.infrastructure.database.session import create_engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup/shutdown."""
    config: FlipFlowConfig = app.state.config
    engine = create_engine(config)

    # Create tables (dev/mock mode only; production uses alembic)
    if config.ebay_mode == "mock":
        import flipflow.core.models  # noqa: F401
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    app.state.engine = engine
    logger.info("FlipFlow started (mode=%s)", config.ebay_mode)
    yield

    # Cleanup: close real eBay client if it exists
    if hasattr(app.state, "_ebay_client"):
        await app.state._ebay_client.close()
    await engine.dispose()
    logger.info("FlipFlow shutdown complete")


def create_app(config: FlipFlowConfig | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    if config is None:
        config = FlipFlowConfig(_env_file=None)

    setup_logging()

    app = FastAPI(
        title="FlipFlow API",
        description="Algorithmic Asset Manager for eBay Listings",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.config = config

    # API key auth — only enabled when api_key is set
    if config.api_key:
        from flipflow.api.middleware import ApiKeyMiddleware
        app.add_middleware(ApiKeyMiddleware, api_key=config.api_key)

    # CORS — configurable origins (defaults to localhost for dev)
    origins = [o.strip() for o in config.cors_allowed_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(health.router, prefix="/api/v1", tags=["health"])
    app.include_router(listings.router, prefix="/api/v1", tags=["listings"])
    app.include_router(zombies.router, prefix="/api/v1", tags=["zombies"])
    app.include_router(queue.router, prefix="/api/v1", tags=["queue"])
    app.include_router(repricer.router, prefix="/api/v1", tags=["repricer"])
    app.include_router(relister.router, prefix="/api/v1", tags=["relister"])
    app.include_router(offers.router, prefix="/api/v1", tags=["offers"])

    return app

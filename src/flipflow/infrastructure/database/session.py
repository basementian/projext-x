"""SQLAlchemy async engine and session factory."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from flipflow.core.config import FlipFlowConfig


def create_engine(config: FlipFlowConfig):
    """Create an async SQLAlchemy engine from config."""
    connect_args = {}
    if config.database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    return create_async_engine(
        config.database_url,
        echo=False,
        connect_args=connect_args,
    )


def create_session_factory(config: FlipFlowConfig) -> async_sessionmaker[AsyncSession]:
    """Create an async session factory."""
    engine = create_engine(config)
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db(session_factory: async_sessionmaker[AsyncSession]):
    """Dependency that yields a database session."""
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

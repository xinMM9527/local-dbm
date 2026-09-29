"""Dynamic async engine management for multiple database connections."""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from typing import Optional


_engines: dict[str, AsyncEngine] = {}


def build_url(conn: dict) -> str:
    db_type = conn["type"]
    user = conn["username"]
    password = conn["password"]
    host = conn["host"]
    port = conn["port"]
    database = conn["database"]

    if db_type == "mysql":
        return f"mysql+asyncmy://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"
    elif db_type == "postgresql":
        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"
    else:
        raise ValueError(f"Unsupported database type: {db_type}")


async def get_engine(conn: dict) -> AsyncEngine:
    conn_id = conn["id"]
    if conn_id not in _engines:
        url = build_url(conn)
        _engines[conn_id] = create_async_engine(url, pool_pre_ping=True, pool_size=2)
    return _engines[conn_id]


async def test_connection(conn: dict) -> bool:
    """Test connectivity by creating a temporary engine and running a simple query."""
    url = build_url(conn)
    engine = create_async_engine(url, pool_pre_ping=True)
    try:
        async with engine.connect() as c:
            from sqlalchemy import text
            await c.execute(text("SELECT 1"))
        return True
    finally:
        await engine.dispose()


async def dispose_engine(conn_id: str):
    if conn_id in _engines:
        await _engines[conn_id].dispose()
        del _engines[conn_id]

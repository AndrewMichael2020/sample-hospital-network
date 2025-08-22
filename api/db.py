"""
Database connection and session management.
"""

import asyncmy
from asyncmy import cursors as asyncmy_cursors
from typing import AsyncGenerator
from contextlib import asynccontextmanager
from .config import settings


# Database connection pool
_connection_pool = None


async def init_db():
    """Initialize database connection pool."""
    global _connection_pool
    _connection_pool = await asyncmy.create_pool(
        host=settings.mysql_host,
        port=settings.mysql_port,
        user=settings.mysql_user,
        password=settings.mysql_password,
        db=settings.mysql_database,
        charset='utf8mb4',
        autocommit=True,
        maxsize=10,
        minsize=1
    )


async def close_db():
    """Close database connection pool."""
    global _connection_pool
    if _connection_pool:
        _connection_pool.close()
        await _connection_pool.wait_closed()
        _connection_pool = None


@asynccontextmanager
async def get_db_connection():
    """Get database connection from pool."""
    if not _connection_pool:
        await init_db()
    
    connection = await _connection_pool.acquire()
    try:
        yield connection
    finally:
        _connection_pool.release(connection)


async def execute_query(query: str, params=None) -> list:
    """Execute a SELECT query and return results."""
    async with get_db_connection() as conn:
        cursor = await conn.cursor()
        try:
            await cursor.execute(query, params or ())
            result = await cursor.fetchall()
            return result
        finally:
            await cursor.close()


async def execute_query_dict(query: str, params=None) -> list:
    """Execute a SELECT query and return results as dictionaries."""
    async with get_db_connection() as conn:
        # asyncmy exposes cursor classes under asyncmy.cursors
        # When passing a cursor class, conn.cursor may return a cursor object directly
        # so do not await it.
        cursor = conn.cursor(cursor=asyncmy_cursors.DictCursor)
        try:
            await cursor.execute(query, params or ())
            result = await cursor.fetchall()
            return result
        finally:
            await cursor.close()
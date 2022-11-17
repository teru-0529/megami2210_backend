#!/usr/bin/python3
# database.py

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import ASYNC_URL, SYNC_URL


class AsyncCon:
    url: str

    def __init__(self, url: str = ASYNC_URL) -> None:
        self.url = url

    def engine(self, echo: bool = True) -> AsyncEngine:
        return create_async_engine(self.url, echo=echo)

    def session(self, echo: bool = True) -> AsyncSession:
        return sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine(echo),
            class_=AsyncSession,
        )


class SyncCon:
    url: str

    def __init__(self, url: str = SYNC_URL) -> None:
        self.url = url

    def engine(self, echo: bool = True) -> Engine:
        return create_engine(self.url, echo=echo)


async def get_session():  # pragma: no cover
    con = AsyncCon()
    async with con.session()() as session:
        yield session

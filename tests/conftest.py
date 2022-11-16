#!/usr/bin/python3
# conftest.py


import os

import alembic
import pytest
import pytest_asyncio
from alembic.config import Config
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import ASYNC_DIALECT, SYNC_DIALECT, db_url
from app.core.database import AsyncCon, SyncCon, get_session

SERVER = "testDB"
SYNC_URL = db_url(dialect=SYNC_DIALECT, server=SERVER)
ASYNC_URL = db_url(dialect=ASYNC_DIALECT, server=SERVER)

config = Config("alembic.ini")


@pytest.fixture
def schema() -> None:
    # test用DBにスキーマ作成
    os.environ["CONTAINER_DSN"] = SYNC_URL
    alembic.command.downgrade(config, "base")
    alembic.command.upgrade(config, "head")


@pytest.fixture
def session(schema) -> AsyncSession:
    # test用非同期sessionを作成
    con = AsyncCon(url=ASYNC_URL)
    return con.session()()


@pytest.fixture
def s_engine(schema) -> Engine:
    # test用同期engineを作成
    con = SyncCon(url=SYNC_URL)
    return con.engine()


@pytest.fixture
def app() -> FastAPI:
    from app.api.server import get_application

    return get_application()


@pytest_asyncio.fixture
async def client(app: FastAPI, session: AsyncSession) -> AsyncClient:

    # DIを使ってFastAPIのDBの向き先をテスト用DBに変更
    async def get_test_session():
        async with session:
            yield session

    app.dependency_overrides[get_session] = get_test_session

    # テスト用に非同期HTTPクライアントを返却
    async with AsyncClient(
        app=app,
        base_url="http://testserver",
        headers={"Content-Type": "application/json"},
    ) as client:
        yield client

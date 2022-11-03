#!/usr/bin/python3
# conftest.py


import os

import asyncio
import alembic
import pytest
import pytest_asyncio
from alembic.config import Config
from app.api.server import app as api_app
from app.core.config import TEST_DB_ASYNC_URL, TEST_DB_SYNC_URL
from app.db.database import get_db
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

config = Config("alembic.ini")


# TODO:https://github.com/pytest-dev/pytest-asyncio/issues/38
@pytest.yield_fixture(scope="session")
def event_loop(request):
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def app(event_loop) -> FastAPI:
    from app.api.server import get_application

    return get_application()


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncClient:

    # Async用のengineとsessionを作成
    async_engine = create_async_engine(TEST_DB_ASYNC_URL, echo=True)
    async_session = sessionmaker(
        autocommit=False, autoflush=False, bind=async_engine, class_=AsyncSession
    )

    # テスト用にオンメモリのSQLiteテーブルを初期化（関数ごとにリセット）FIXME:
    os.environ["CONTAINER_DSN"] = TEST_DB_SYNC_URL
    alembic.command.downgrade(config, "base")
    alembic.command.upgrade(config, "head")

    # DIを使ってFastAPIのDBの向き先をテスト用DBに変更
    async def get_test_db():
        async with async_session() as session:
            yield session

    api_app.dependency_overrides[get_db] = get_test_db

    # テスト用に非同期HTTPクライアントを返却
    async with AsyncClient(
        app=app,
        base_url="http://testserver",
        headers={"Content-Type": "application/json"},
    ) as client:
        yield client

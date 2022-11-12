#!/usr/bin/python3
# conftest.py


import os

import alembic
import pytest
import pytest_asyncio
from alembic.config import Config
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import TEST_DB_ASYNC_URL, TEST_DB_SYNC_URL
from app.db.database import get_db

config = Config("alembic.ini")


@pytest.fixture
def schema() -> None:
    # test用DBにスキーマ作成
    os.environ["CONTAINER_DSN"] = TEST_DB_SYNC_URL
    alembic.command.downgrade(config, "base")
    alembic.command.upgrade(config, "head")


@pytest.fixture
def async_db(schema) -> AsyncSession:
    # test用非同期engineとsessionを作成
    async_engine = create_async_engine(TEST_DB_ASYNC_URL, echo=True)
    async_session = sessionmaker(
        autocommit=False, autoflush=False, bind=async_engine, class_=AsyncSession
    )
    return async_session()


@pytest.fixture
def sync_engine(schema) -> Engine:
    # test用同期engineを作成
    sync_engine = create_engine(TEST_DB_SYNC_URL, echo=True)
    return sync_engine


@pytest.fixture
def app() -> FastAPI:
    from app.api.server import get_application

    return get_application()


@pytest_asyncio.fixture
async def client(app: FastAPI, async_db: AsyncSession) -> AsyncClient:

    # DIを使ってFastAPIのDBの向き先をテスト用DBに変更
    async def get_test_db():
        async with async_db as session:
            yield session

    app.dependency_overrides[get_db] = get_test_db

    # テスト用に非同期HTTPクライアントを返却
    async with AsyncClient(
        app=app,
        base_url="http://testserver",
        headers={"Content-Type": "application/json"},
    ) as client:
        yield client

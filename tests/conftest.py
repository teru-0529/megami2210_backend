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

from app.api.schemas.accounts import AccountCreate, ProfileInDB, ProfileBaseUpdate
from app.core.config import ASYNC_DIALECT, JWT_TOKEN_PREFIX, SYNC_DIALECT, db_url
from app.core.database import AsyncCon, SyncCon, get_session
from app.services import auth_service
from app.services.accounts import AccountService
from app.repositries.accounts import AccountRepository
from app.models.segment_values import AccountTypes

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
async def non_active_account(session: AsyncSession) -> ProfileInDB:
    # 未アクティベート
    new_user = AccountCreate(
        user_name="織田信長",
        email="oda@sengoku.com",
        init_password="testPassword",
    )
    service = AccountService()
    account = await service.create(session=session, id="T-000", new_account=new_user)
    yield account
    await service.delete(session=session, id=account.account_id)


@pytest_asyncio.fixture
async def general_account(
    session: AsyncSession, non_active_account: ProfileInDB
) -> ProfileInDB:
    # アクティベート済（account_type:GENERAL）
    repo = AccountRepository()
    await repo.password_change(
        session=session, id=non_active_account.account_id, new_password="password"
    )
    service = AccountService()
    account = await service.get_by_id(session=session, id=non_active_account.account_id)
    yield account


@pytest_asyncio.fixture
async def provisional_account(
    session: AsyncSession, general_account: ProfileInDB
) -> ProfileInDB:
    # アクティベート済（account_type:PROVISIONAL)
    patch_params = ProfileBaseUpdate(account_type=AccountTypes.provisional)
    service = AccountService()
    account = await service.patch_base_profile(
        session=session, id=general_account.account_id, patch_params=patch_params
    )
    yield account


@pytest_asyncio.fixture
async def admin_account(
    session: AsyncSession, general_account: ProfileInDB
) -> ProfileInDB:
    # アクティベート済（account_type:ADMINISTRATOR)
    patch_params = ProfileBaseUpdate(account_type=AccountTypes.administrator)
    service = AccountService()
    account = await service.patch_base_profile(
        session=session, id=general_account.account_id, patch_params=patch_params
    )
    yield account


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


@pytest.fixture
def non_active_client(
    client: AsyncClient, non_active_account: ProfileInDB
) -> AsyncClient:
    token = auth_service.create_token_for_user(account=non_active_account)
    client.headers = {
        **client.headers,
        "Authorization": f"{JWT_TOKEN_PREFIX} {token}",
    }
    yield client


@pytest.fixture
def general_client(client: AsyncClient, general_account: ProfileInDB) -> AsyncClient:
    token = auth_service.create_token_for_user(account=general_account)
    client.headers = {
        **client.headers,
        "Authorization": f"{JWT_TOKEN_PREFIX} {token}",
    }
    yield client


@pytest.fixture
def provisional_client(
    client: AsyncClient, provisional_account: ProfileInDB
) -> AsyncClient:
    token = auth_service.create_token_for_user(account=provisional_account)
    client.headers = {
        **client.headers,
        "Authorization": f"{JWT_TOKEN_PREFIX} {token}",
    }
    yield client


@pytest.fixture
def admin_client(client: AsyncClient, admin_account: ProfileInDB) -> AsyncClient:
    token = auth_service.create_token_for_user(account=admin_account)
    client.headers = {
        **client.headers,
        "Authorization": f"{JWT_TOKEN_PREFIX} {token}",
    }
    yield client


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


def assert_profile(actual: ProfileInDB, expected: ProfileInDB) -> None:
    assert actual.account_id == expected.account_id
    assert actual.account_type == expected.account_type
    assert actual.email == expected.email
    assert actual.user_name == expected.user_name
    assert actual.nickname == expected.nickname

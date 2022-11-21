#!/usr/bin/python3
# test_accounts.py

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.routing import NoMatchFound
from starlette.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from app.api.schemas.accounts import UserCreate, UserPublic
from app.models.segment_values import AccountTypes
from app.services.accounts import AccountService

pytestmark = pytest.mark.asyncio
is_regression = True


@pytest_asyncio.fixture
async def tmp_account(session: AsyncSession) -> UserPublic:
    new_user = UserCreate(
        user_name="織田信長",
        email="oda@sengoku.com",
    )
    service = AccountService()
    created_user = await service.create(
        session=session, id="T-000", new_account=new_user
    )
    return created_user


@pytest.mark.skipif(not is_regression, reason="not regression phase")
class TestRouteExists:
    async def test_create_route(self, app: FastAPI, client: AsyncClient) -> None:
        try:
            await client.put(app.url_path_for("accounts:create", id="T-001"), json={})
        except NoMatchFound:
            pytest.fail("route not exist")


@pytest.mark.skipif(not is_regression, reason="not regression phase")
class TestCreate:

    # 正常ケースパラメータ
    valid_params = {
        "<body:full>": (
            "T-001",
            UserCreate(
                user_name="織田信長",
                email="oda@sengoku.com",
                account_type=AccountTypes.administrator,
            ),
        ),
        "<body:account_type>:任意入力": (
            "T-001",
            UserCreate(
                user_name="織田信長",
                email="oda@sengoku.com",
            ),
        ),
    }

    @pytest.mark.parametrize(
        "param", list(valid_params.values()), ids=list(valid_params.keys())
    )
    async def test_ok_case(
        self,
        app: FastAPI,
        client: AsyncClient,
        param: tuple[str, UserCreate],
    ) -> None:

        res = await client.put(
            app.url_path_for("accounts:create", id=param[0]),
            data=param[1].json(exclude_unset=True),
        )

        assert res.status_code == HTTP_200_OK
        dict = res.json()
        assert dict["account_id"] == param[0]
        assert dict["user_name"] == param[1].user_name
        assert dict["email"] == param[1].email
        assert (dict["account_type"] == param[1].account_type) or (
            dict["account_type"] == AccountTypes.general
            and param[1].account_type is None
        )

    # 異常ケースパラメータ
    invalid_params = {
        "<path:id>:桁数不足": (
            "00",
            '{"user_name":"武田信玄","email":"shingen@sengoku.com"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<path:id>:桁数超過": (
            "000000",
            '{"user_name":"武田信玄","email":"shingen@sengoku.com"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<path:id>:None": (
            None,
            '{"user_name":"武田信玄","email":"shingen@sengoku.com"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:user_name>:桁数超過": (
            "T-100",
            '{"user_name":"000000000100000000020000000003","email":"shingen@sengoku.com"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:user_name>:None": (
            "T-100",
            '{"user_name":None,"email":"shingen@sengoku.com"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:user_name>:項目なし": (
            "T-100",
            '{"email":"shingen@sengoku.com"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:email>:フォーマット不正①": (
            "T-100",
            '{"user_name":"武田信玄","email":"shingen.sengoku"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:email>:フォーマット不正②": (
            "T-100",
            '{"user_name":"武田信玄","email":"sengoku.com"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:email>:フォーマット不正③": (
            "T-100",
            '{"user_name":"武田信玄","email":"shingen@takeda@com"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:email>:None": (
            "T-100",
            '{"user_name":"武田信玄","email":None}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:email>:項目なし": (
            "T-100",
            '{"user_name":"武田信玄"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:account_type>:区分値外": (
            "T-100",
            '{"user_name":"武田信玄","email":"shingen@sengoku.com","account_type":"NO_TYPE"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:account_type>:None": (
            "T-100",
            '{"user_name":"武田信玄","email":"shingen@sengoku.com","account_type":None}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body>:未定義フィールド": (
            "T-100",
            '{"user_name":"武田信玄","email":"shingen@sengoku.com","dummy":"dummy"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
    }

    @pytest.mark.parametrize(
        "param", list(invalid_params.values()), ids=list(invalid_params.keys())
    )
    async def test_ng_case(
        self,
        app: FastAPI,
        client: AsyncClient,
        param: tuple[str, str, int],
    ) -> None:
        res = await client.put(
            app.url_path_for("accounts:create", id=param[0]),
            data=param[1],
        )
        assert res.status_code == param[2]

    # 異常(DB相関)ケースパラメータ
    invalid_db_params = {
        "duplicate:[account_id]": (
            "T-000",
            '{"user_name":"武田信玄","email":"shingen@sengoku.com"}',
            HTTP_400_BAD_REQUEST,
        ),
        "duplicate:[user_name]": (
            "T-100",
            '{"user_name":"織田信長","email":"shingen@sengoku.com"}',
            HTTP_400_BAD_REQUEST,
        ),
        "duplicate:[email]": (
            "T-100",
            '{"user_name":"武田信玄","email":"oda@sengoku.com"}',
            HTTP_400_BAD_REQUEST,
        ),
    }

    @pytest.mark.parametrize(
        "param", list(invalid_db_params.values()), ids=list(invalid_db_params.keys())
    )
    async def test_db_ng_case(
        self,
        app: FastAPI,
        client: AsyncClient,
        param: tuple[str, str, int],
        tmp_account: UserPublic,
    ) -> None:
        res = await client.put(
            app.url_path_for("accounts:create", id=param[0]),
            data=param[1],
        )
        assert res.status_code == param[2]

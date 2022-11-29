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
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from app.api.schemas.accounts import (
    AccountCreate,
    PasswordReset,
    ProfileBaseUpdate,
    ProfileInDB,
)
from app.models.segment_values import AccountTypes
from app.services.accounts import AccountService
from tests.conftest import assert_profile

pytestmark = pytest.mark.asyncio
is_regression = True


@pytest_asyncio.fixture
async def account_for_update(session: AsyncSession) -> ProfileInDB:
    new_user = AccountCreate(
        user_name="徳川家康",
        email="tokugawa@sengoku.com",
        init_password="testPassword",
    )
    service = AccountService()
    created_user = await service.create(
        session=session, id="T-001", new_account=new_user
    )
    yield created_user
    await service.delete(session=session, id=created_user.account_id)


@pytest_asyncio.fixture
async def account_for_delete(session: AsyncSession) -> ProfileInDB:
    new_user = AccountCreate(
        user_name="徳川家康",
        email="tokugawa@sengoku.com",
        init_password="testPassword",
    )
    service = AccountService()
    created_user = await service.create(
        session=session, id="T-001", new_account=new_user
    )
    return created_user


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


@pytest.mark.skipif(not is_regression, reason="not regression phase")
class TestRouteExists:
    async def test_create_route(self, app: FastAPI, client: AsyncClient) -> None:
        try:
            await client.put(app.url_path_for("accounts:create", id="T-001"), json={})
        except NoMatchFound:
            pytest.fail("route not exist")

    async def test_get_route(self, app: FastAPI, client: AsyncClient) -> None:
        try:
            await client.get(app.url_path_for("accounts:get-profile", id="T-001"))
        except NoMatchFound:
            pytest.fail("route not exist")

    async def test_patch_base_profile_route(
        self, app: FastAPI, client: AsyncClient
    ) -> None:
        try:
            await client.patch(
                app.url_path_for("accounts:patch-profile", id="T-001"),
                json={},
            )
        except NoMatchFound:
            pytest.fail("route not exist")

    async def test_delete_route(self, app: FastAPI, client: AsyncClient) -> None:
        try:
            await client.delete(app.url_path_for("accounts:delete", id="T-001"))
        except NoMatchFound:
            pytest.fail("route not exist")

    async def test_password_reset_route(
        self, app: FastAPI, client: AsyncClient
    ) -> None:
        try:
            await client.patch(app.url_path_for("accounts:password-reset", id="T-001"))
        except NoMatchFound:
            pytest.fail("route not exist")


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


@pytest.mark.skipif(not is_regression, reason="not regression phase")
class TestCreate:

    # 正常ケースパラメータ
    valid_params = {
        "<body:full>": (
            "T-001",
            AccountCreate(
                user_name="織田信長",
                email="oda@sengoku.com",
                account_type=AccountTypes.administrator,
                init_password="odanobunaga",
            ),
        ),
        "<body:account_type>:任意入力": (
            "T-001",
            AccountCreate(
                user_name="織田信長", email="oda@sengoku.com", init_password="odanobunaga"
            ),
        ),
        "<body:init_password>:任意入力": (
            "T-001",
            AccountCreate(
                user_name="織田信長",
                email="oda@sengoku.com",
                account_type=AccountTypes.administrator,
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
        param: tuple[str, AccountCreate],
    ) -> None:

        res = await client.put(
            app.url_path_for("accounts:create", id=param[0]),
            data=param[1].json(exclude_unset=True),
        )

        assert res.status_code == HTTP_200_OK
        created_account = ProfileInDB(**res.json())
        assert created_account.account_id == param[0]
        assert created_account.user_name == param[1].user_name
        assert created_account.email == param[1].email
        assert created_account.account_type == param[1].account_type
        assert created_account.is_active is False
        assert created_account.verified_email is False
        assert created_account.nickname is None

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

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
        "<body:init_password>:桁数不足": (
            "T-100",
            '{"user_name":"武田信玄","email":"shingen@sengoku.com","init_password":"pass"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:init_password>:None": (
            "T-100",
            '{"user_name":"武田信玄","email":"shingen@sengoku.com","init_password":None}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body>:未定義フィールド": (
            "T-100",
            '{"user_name":"武田信玄","email":"shingen@sengoku.com","dummy":"dummy"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body>:None": (
            "T-100",
            None,
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

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    # 異常(DB相関)ケースパラメータ
    invalid_db_params = {
        "duplicate:[account_id]": (
            "T-000",
            '{"user_name":"武田信玄","email":"shingen@sengoku.com"}',
            HTTP_409_CONFLICT,
        ),
        "duplicate:[user_name]": (
            "T-100",
            '{"user_name":"織田信長","email":"shingen@sengoku.com"}',
            HTTP_409_CONFLICT,
        ),
        "duplicate:[email]": (
            "T-100",
            '{"user_name":"武田信玄","email":"oda@sengoku.com"}',
            HTTP_409_CONFLICT,
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
        fixed_account: ProfileInDB,
    ) -> None:
        res = await client.put(
            app.url_path_for("accounts:create", id=param[0]),
            data=param[1],
        )
        assert res.status_code == param[2]


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


@pytest.mark.skipif(not is_regression, reason="not regression phase")
class TestGet:
    async def test_ok_case(
        self, app: FastAPI, client: AsyncClient, fixed_account: ProfileInDB
    ) -> None:

        res = await client.get(
            app.url_path_for("accounts:get-profile", id=fixed_account.account_id)
        )
        assert res.status_code == HTTP_200_OK
        profile = ProfileInDB(**res.json())
        assert_profile(actual=profile, expected=fixed_account)

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    # 異常ケースパラメータ
    invalid_params = {
        "<path:id>:桁数不足": (
            "00",
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<path:id>:桁数超過": (
            "000000",
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<path:id>:None": (
            None,
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
        param: tuple[str, int],
    ) -> None:
        res = await client.get(app.url_path_for("accounts:get-profile", id=param[0]))
        assert res.status_code == param[1]


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


@pytest.mark.skipif(not is_regression, reason="not regression phase")
class TestPatchProfile:

    # 正常ケースパラメータ
    valid_params = {
        "<body:user_name>": ProfileBaseUpdate(user_name="徳川家光"),
        "<body:account_type>": ProfileBaseUpdate(account_type=AccountTypes.provisional),
        "複合ケース": ProfileBaseUpdate(
            user_name="徳川家光", account_type=AccountTypes.administrator
        ),
    }

    @pytest.mark.parametrize(
        "update_params", list(valid_params.values()), ids=list(valid_params.keys())
    )
    async def test_ok_case(
        self,
        app: FastAPI,
        client: AsyncClient,
        account_for_update: ProfileInDB,
        update_params: ProfileBaseUpdate,
    ) -> None:
        res = await client.patch(
            app.url_path_for(
                "accounts:patch-profile", id=account_for_update.account_id
            ),
            data=update_params.json(exclude_unset=True),
        )
        assert res.status_code == HTTP_200_OK
        updated_account = ProfileInDB(**res.json())

        update_dict = update_params.dict(exclude_unset=True)
        expected = account_for_update.copy(update=update_dict)
        assert_profile(actual=updated_account, expected=expected)

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    # 異常ケースパラメータ
    invalid_params = {
        "<path:id>:存在しない": ("T-XXX", '{"user_name":"DUMMY"}', HTTP_404_NOT_FOUND),
        "<path:id>:桁数不足": (
            "00",
            "{}",
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<path:id>:桁数超過": (
            "000000",
            "{}",
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<path:id>:None": (
            None,
            "{}",
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:user_name>:桁数超過": (
            "T-100",
            '{"user_name":"000000000100000000020000000003"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:user_name>:None": (
            "T-100",
            '{"user_name":null}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:account_type>:区分値外": (
            "T-100",
            '{"account_type":"NO_TYPE"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:account_type>:None": (
            "T-100",
            '{"account_type":null}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body>:変更不可フィールド(email)": (
            "T-100",
            '{"email":"shingen@sengoku.com"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body>:None": (
            "T-100",
            None,
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
        res = await client.patch(
            app.url_path_for("accounts:patch-profile", id=param[0]),
            data=param[1],
        )
        assert res.status_code == param[2]

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    # 異常(DB相関)ケースパラメータ
    invalid_db_params = {
        "duplicate:[user_name]": (
            '{"user_name":"織田信長"}',
            HTTP_409_CONFLICT,
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
        fixed_account: ProfileInDB,
        account_for_update: ProfileInDB,
    ) -> None:
        res = await client.patch(
            app.url_path_for(
                "accounts:patch-profile", id=account_for_update.account_id
            ),
            data=param[0],
        )
        assert res.status_code == param[1]


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


@pytest.mark.skipif(not is_regression, reason="not regression phase")
class TestDelete:
    async def test_ok_case(
        self, app: FastAPI, client: AsyncClient, account_for_delete: ProfileInDB
    ) -> None:

        res = await client.delete(
            app.url_path_for("accounts:delete", id=account_for_delete.account_id)
        )
        assert res.status_code == HTTP_200_OK
        profile = ProfileInDB(**res.json())
        assert_profile(actual=profile, expected=account_for_delete)

        # 再検索して存在しないこと
        res = await client.get(
            app.url_path_for("accounts:get-profile", id=account_for_delete.account_id)
        )
        assert res.status_code == HTTP_404_NOT_FOUND

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    # 異常ケースパラメータ
    invalid_params = {
        "<path:id>:存在しない": (
            "T-XXX",
            HTTP_404_NOT_FOUND,
        ),
        "<path:id>:桁数不足": (
            "00",
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<path:id>:桁数超過": (
            "000000",
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<path:id>:None": (
            None,
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
        param: tuple[str, int],
    ) -> None:
        res = await client.delete(app.url_path_for("accounts:delete", id=param[0]))
        assert res.status_code == param[1]


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


@pytest.mark.skipif(not is_regression, reason="not regression phase")
class TestResetPassword:
    # 正常ケース
    async def test_ok_case(
        self,
        app: FastAPI,
        client: AsyncClient,
        account_for_update: ProfileInDB,
    ) -> None:
        update_param = PasswordReset(init_password="new_password")

        login_data = {
            "username": account_for_update.account_id,
            "password": update_param.init_password,
        }

        # リセット前はリセットパスワードでログインできないこと
        client.headers["content-type"] = "application/x-www-form-urlencoded"
        res = await client.post(app.url_path_for("mine:login"), data=login_data)
        assert res.status_code == HTTP_401_UNAUTHORIZED

        client.headers["content-type"] = ""
        res = await client.patch(
            app.url_path_for(
                "accounts:password-reset", id=account_for_update.account_id
            ),
            data=update_param.json(exclude_unset=True),
        )
        print(res.json())
        assert res.status_code == HTTP_200_OK

        # リセット後はリセットパスワードでログインできること
        client.headers["content-type"] = "application/x-www-form-urlencoded"
        res = await client.post(app.url_path_for("mine:login"), data=login_data)
        assert res.status_code == HTTP_200_OK

        # リセット後のアカウントが非アクティベート状態であること
        res = await client.get(
            app.url_path_for("accounts:get-profile", id=account_for_update.account_id)
        )
        assert res.status_code == HTTP_200_OK
        profile = ProfileInDB(**res.json())
        profile.is_active is False

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    # 異常ケースパラメータ
    invalid_params = {
        "<body:init_password>:桁数不足": (
            '{"init_password":"pass"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:init_password>:None": (
            '{"init_password":None}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body>:設定不可フィールド(dummy)": (
            '{"dummy":"dummy"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body>:None": (
            None,
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
        param: tuple[str, int],
    ) -> None:
        res = await client.patch(
            app.url_path_for("accounts:password-reset", id="T-001"), data=param[0]
        )
        assert res.status_code == param[1]

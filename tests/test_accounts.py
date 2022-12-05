#!/usr/bin/python3
# test_accounts.py

from typing import List

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient
from pandas import DataFrame, read_csv
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.routing import NoMatchFound
from starlette.status import (
    HTTP_200_OK,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from app.api.schemas.accounts import (
    AccountCreate,
    PasswordReset,
    ProfileBaseUpdate,
    ProfileInDB,
    ProfilePublicList,
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


@pytest.fixture
def import_profile(s_engine: Engine) -> DataFrame:
    datas: DataFrame = read_csv(
        "tests/data/test_profile_data.csv", encoding="utf-8", dtype={5: str}
    )
    datas.to_sql(
        name="profiles",
        con=s_engine,
        schema="account",
        if_exists="append",
        index=False,
    )
    return datas


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


@pytest.mark.skipif(not is_regression, reason="not regression phase")
class TestRouteExists:
    async def test_create(self, app: FastAPI, client: AsyncClient) -> None:
        try:
            await client.put(app.url_path_for("accounts:create", id="T-001"), json={})
        except NoMatchFound:
            pytest.fail("route not exist")

    async def test_get_profile(self, app: FastAPI, client: AsyncClient) -> None:
        try:
            await client.get(app.url_path_for("accounts:get-profile", id="T-001"))
        except NoMatchFound:
            pytest.fail("route not exist")

    async def test_patch_profile(self, app: FastAPI, client: AsyncClient) -> None:
        try:
            await client.patch(
                app.url_path_for("accounts:patch-profile", id="T-001"),
                json={},
            )
        except NoMatchFound:
            pytest.fail("route not exist")

    async def test_delete(self, app: FastAPI, client: AsyncClient) -> None:
        try:
            await client.delete(app.url_path_for("accounts:delete", id="T-001"))
        except NoMatchFound:
            pytest.fail("route not exist")

    async def test_password_reset(self, app: FastAPI, client: AsyncClient) -> None:
        try:
            await client.patch(app.url_path_for("accounts:password-reset", id="T-001"))
        except NoMatchFound:
            pytest.fail("route not exist")

    async def test_search_profile(self, app: FastAPI, client: AsyncClient) -> None:
        try:
            await client.post(app.url_path_for("accounts:search-profile"))
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
                user_name="徳川家康",
                email="tokugawa@sengoku.com",
                account_type=AccountTypes.administrator,
                init_password="password",
            ),
        ),
        "<body:account_type>:任意入力": (
            "T-001",
            AccountCreate(
                user_name="徳川家康", email="tokugawa@sengoku.com", init_password="password"
            ),
        ),
        "<body:init_password>:任意入力": (
            "T-001",
            AccountCreate(
                user_name="徳川家康",
                email="tokugawa@sengoku.com",
                account_type=AccountTypes.administrator,
            ),
        ),
    }

    @pytest.mark.parametrize(
        "param", list(valid_params.values()), ids=list(valid_params.keys())
    )
    # 正常ケース
    async def test_ok(
        self,
        app: FastAPI,
        admin_client: AsyncClient,
        param: tuple[str, AccountCreate],
    ) -> None:

        res = await admin_client.put(
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

    # 異常ケース（アクティベーションエラー）
    async def test_ng_activation(
        self, app: FastAPI, non_active_client: AsyncClient
    ) -> None:
        res = await non_active_client.put(
            app.url_path_for("accounts:create", id="T-000"),
            data='{"user_name":"武田信玄","email":"shingen@sengoku.com"}',
        )
        assert res.status_code == HTTP_401_UNAUTHORIZED

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    # 異常ケース（認可エラー）
    async def test_ng_permission(
        self, app: FastAPI, general_client: AsyncClient
    ) -> None:
        res = await general_client.put(
            app.url_path_for("accounts:create", id="T-000"),
            data='{"user_name":"武田信玄","email":"shingen@sengoku.com"}',
        )
        assert res.status_code == HTTP_403_FORBIDDEN

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
    # 異常ケース（重複エラー）
    async def test_ng_duplicate(
        self,
        app: FastAPI,
        admin_client: AsyncClient,
        param: tuple[str, str, int],
    ) -> None:
        res = await admin_client.put(
            app.url_path_for("accounts:create", id=param[0]),
            data=param[1],
        )
        assert res.status_code == param[2]

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
    # 異常ケース（バリデーションエラー）
    async def test_ng_validation(
        self,
        app: FastAPI,
        admin_client: AsyncClient,
        param: tuple[str, str, int],
    ) -> None:
        res = await admin_client.put(
            app.url_path_for("accounts:create", id=param[0]),
            data=param[1],
        )
        assert res.status_code == param[2]


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


@pytest.mark.skipif(not is_regression, reason="not regression phase")
class TestGet:

    # 正常ケース
    async def test_ok(
        self, app: FastAPI, admin_client: AsyncClient, admin_account: ProfileInDB
    ) -> None:

        res = await admin_client.get(
            app.url_path_for("accounts:get-profile", id=admin_account.account_id)
        )
        assert res.status_code == HTTP_200_OK
        profile = ProfileInDB(**res.json())
        assert_profile(actual=profile, expected=admin_account)

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    # 異常ケース（アクティベーションエラー）
    async def test_ng_activation(
        self, app: FastAPI, non_active_client: AsyncClient
    ) -> None:
        res = await non_active_client.get(
            app.url_path_for("accounts:get-profile", id="T-000"),
        )
        assert res.status_code == HTTP_401_UNAUTHORIZED

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    # 異常ケース（認可エラー）
    async def test_ng_permission(
        self, app: FastAPI, provisional_client: AsyncClient
    ) -> None:
        res = await provisional_client.get(
            app.url_path_for("accounts:get-profile", id="T-000"),
        )
        assert res.status_code == HTTP_403_FORBIDDEN

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
    # 異常ケース（バリデーションエラー）
    async def test_ng_validation(
        self,
        app: FastAPI,
        admin_client: AsyncClient,
        param: tuple[str, int],
    ) -> None:
        res = await admin_client.get(
            app.url_path_for("accounts:get-profile", id=param[0])
        )
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
    # 正常ケース
    async def test_ok(
        self,
        app: FastAPI,
        admin_client: AsyncClient,
        account_for_update: ProfileInDB,
        update_params: ProfileBaseUpdate,
    ) -> None:
        res = await admin_client.patch(
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

    # 異常ケース（アクティベーションエラー）
    async def test_ng_activation(
        self, app: FastAPI, non_active_client: AsyncClient
    ) -> None:
        res = await non_active_client.patch(
            app.url_path_for("accounts:patch-profile", id="T-000"),
            data='{"user_name":"武田信玄"}',
        )
        assert res.status_code == HTTP_401_UNAUTHORIZED

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    # 異常ケース（認可エラー）
    async def test_ng_permission(
        self, app: FastAPI, general_client: AsyncClient
    ) -> None:
        res = await general_client.patch(
            app.url_path_for("accounts:patch-profile", id="T-000"),
            data='{"user_name":"武田信玄"}',
        )
        assert res.status_code == HTTP_403_FORBIDDEN

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
    # 異常ケース（重複エラー）
    async def test_ng_duplicate(
        self,
        app: FastAPI,
        admin_client: AsyncClient,
        admin_account: ProfileInDB,
        param: tuple[str, str, int],
        account_for_update: ProfileInDB,
    ) -> None:
        res = await admin_client.patch(
            app.url_path_for(
                "accounts:patch-profile", id=account_for_update.account_id
            ),
            data=param[0],
        )
        assert res.status_code == param[1]

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
    # 異常ケース（バリデーションエラー）
    async def test_ng_validation(
        self,
        app: FastAPI,
        admin_client: AsyncClient,
        param: tuple[str, str, int],
    ) -> None:
        res = await admin_client.patch(
            app.url_path_for("accounts:patch-profile", id=param[0]),
            data=param[1],
        )
        assert res.status_code == param[2]


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


@pytest.mark.skipif(not is_regression, reason="not regression phase")
class TestDelete:

    # 正常ケース
    async def test_ok(
        self, app: FastAPI, admin_client: AsyncClient, account_for_delete: ProfileInDB
    ) -> None:

        res = await admin_client.delete(
            app.url_path_for("accounts:delete", id=account_for_delete.account_id)
        )
        assert res.status_code == HTTP_200_OK
        profile = ProfileInDB(**res.json())
        assert_profile(actual=profile, expected=account_for_delete)

        # 再検索して存在しないこと
        res = await admin_client.get(
            app.url_path_for("accounts:get-profile", id=account_for_delete.account_id)
        )
        assert res.status_code == HTTP_404_NOT_FOUND

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    # 異常ケース（アクティベーションエラー）
    async def test_ng_activation(
        self, app: FastAPI, non_active_client: AsyncClient
    ) -> None:
        res = await non_active_client.delete(
            app.url_path_for("accounts:delete", id="T-000")
        )
        assert res.status_code == HTTP_401_UNAUTHORIZED

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    # 異常ケース（認可エラー）
    async def test_ng_permission(
        self, app: FastAPI, general_client: AsyncClient
    ) -> None:
        res = await general_client.delete(
            app.url_path_for("accounts:delete", id="T-000")
        )
        assert res.status_code == HTTP_403_FORBIDDEN

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
    # 異常ケース（バリデーションエラー）
    async def test_ng_validation(
        self,
        app: FastAPI,
        admin_client: AsyncClient,
        param: tuple[str, int],
    ) -> None:
        res = await admin_client.delete(
            app.url_path_for("accounts:delete", id=param[0])
        )
        assert res.status_code == param[1]


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


@pytest.mark.skipif(not is_regression, reason="not regression phase")
class TestResetPassword:

    # 正常ケース
    async def test_ok(
        self,
        app: FastAPI,
        admin_client: AsyncClient,
        account_for_update: ProfileInDB,
    ) -> None:
        update_param = PasswordReset(init_password="new_password")

        login_data = {
            "username": account_for_update.account_id,
            "password": update_param.init_password,
        }

        # リセット前はリセットパスワードでログインできないこと
        admin_client.headers["content-type"] = "application/x-www-form-urlencoded"
        res = await admin_client.post(app.url_path_for("mine:login"), data=login_data)
        assert res.status_code == HTTP_401_UNAUTHORIZED

        admin_client.headers["content-type"] = ""
        res = await admin_client.patch(
            app.url_path_for(
                "accounts:password-reset", id=account_for_update.account_id
            ),
            data=update_param.json(exclude_unset=True),
        )
        assert res.status_code == HTTP_200_OK

        # リセット後はリセットパスワードでログインできること
        admin_client.headers["content-type"] = "application/x-www-form-urlencoded"
        res = await admin_client.post(app.url_path_for("mine:login"), data=login_data)
        assert res.status_code == HTTP_200_OK

        # リセット後のアカウントが非アクティベート状態であること
        res = await admin_client.get(
            app.url_path_for("accounts:get-profile", id=account_for_update.account_id)
        )
        assert res.status_code == HTTP_200_OK
        profile = ProfileInDB(**res.json())
        profile.is_active is False

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    # 異常ケース（アクティベーションエラー）
    async def test_ng_activation(
        self, app: FastAPI, non_active_client: AsyncClient
    ) -> None:
        res = await non_active_client.patch(
            app.url_path_for("accounts:password-reset", id="T-000"),
            data='{"init_password":"password"}',
        )
        assert res.status_code == HTTP_401_UNAUTHORIZED

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    # 異常ケース（認可エラー）
    async def test_ng_permission(
        self, app: FastAPI, general_client: AsyncClient
    ) -> None:
        res = await general_client.patch(
            app.url_path_for("accounts:password-reset", id="T-000"),
            data='{"init_password":"password"}',
        )
        assert res.status_code == HTTP_403_FORBIDDEN

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
    # 異常ケース（バリデーションエラー）
    async def test_ng_validation(
        self,
        app: FastAPI,
        admin_client: AsyncClient,
        param: tuple[str, int],
    ) -> None:
        res = await admin_client.patch(
            app.url_path_for("accounts:password-reset", id="T-001"), data=param[0]
        )
        assert res.status_code == param[1]


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


@pytest.mark.skipif(not is_regression, reason="not regression phase")
class TestSearch:

    # 正常ケースパラメータ
    valid_params = {
        "パラメータ無し": (
            {},
            "{}",
            24,
            10,
            [
                "D-001",
                "D-002",
                "D-003",
                "D-004",
                "D-005",
                "D-101",
                "D-102",
                "D-103",
                "D-104",
                "D-105",
            ],
        ),
        "<query:limit>:(100)": (
            {"limit": 100},
            "{}",
            24,
            24,
            [
                "D-001",
                "D-002",
                "D-003",
                "D-004",
                "D-005",
                "D-101",
                "D-102",
                "D-103",
                "D-104",
                "D-105",
                "E-001",
                "E-002",
                "E-003",
                "E-004",
                "E-005",
                "E-301",
                "E-302",
                "E-303",
                "E-304",
                "E-305",
                "T-000",
                "T-901",
                "T-902",
                "T-903",
            ],
        ),
        "<query:limit>:(3)": (
            {"limit": 3},
            "{}",
            24,
            3,
            [
                "D-001",
                "D-002",
                "D-003",
            ],
        ),
        "<query:offset>:(5)": (
            {"offset": 5},
            "{}",
            24,
            10,
            [
                "D-101",
                "D-102",
                "D-103",
                "D-104",
                "D-105",
                "E-001",
                "E-002",
                "E-003",
                "E-004",
                "E-005",
            ],
        ),
        "<query:offset>:(30)": (
            {"offset": 30},
            "{}",
            24,
            0,
            [],
        ),
        "<query:sort>:(-account_id)": (
            {"sort": "-account_id"},
            "{}",
            24,
            10,
            [
                "T-903",
                "T-902",
                "T-901",
                "T-000",
                "E-305",
                "E-304",
                "E-303",
                "E-302",
                "E-301",
                "E-005",
            ],
        ),
        "<query:sort>:(+account_type)": (
            {"sort": "+account_type"},
            "{}",
            24,
            10,
            [
                "D-001",
                "D-002",
                "D-102",
                "E-302",
                "T-901",
                "D-003",
                "D-004",
                "D-103",
                "D-104",
                "D-105",
            ],
        ),
        "<body:account_id_sw>:(E-0)": (
            {},
            '{"account_id_sw": "E-0"}',
            5,
            5,
            [
                "E-001",
                "E-002",
                "E-003",
                "E-004",
                "E-005",
            ],
        ),
        "<body:user_name_cn>:(徳川)": (
            {},
            '{"user_name_cn": "徳川"}',
            4,
            4,
            [
                "D-002",
                "D-003",
                "D-004",
                "D-005",
            ],
        ),
        "<body:nickname_cn>:(組長)": (
            {},
            '{"nickname_cn": "組長"}',
            3,
            3,
            [
                "E-303",
                "E-304",
                "E-305",
            ],
        ),
        "<body:nickname_ex>:(true)": (
            {},
            '{"nickname_ex": true}',
            12,
            10,
            [
                "D-001",
                "D-002",
                "D-004",
                "D-103",
                "E-004",
                "E-301",
                "E-302",
                "E-303",
                "E-304",
                "E-305",
            ],
        ),
        "<body:nickname_ex>:(false)": (
            {},
            '{"nickname_ex": false}',
            12,
            10,
            [
                "D-003",
                "D-005",
                "D-101",
                "D-102",
                "D-104",
                "D-105",
                "E-001",
                "E-002",
                "E-003",
                "E-005",
            ],
        ),
        "<body:email_dm>:(bakumatsu.com)": (
            {},
            '{"email_dm": "bakumatsu.com"}',
            8,
            8,
            [
                "E-001",
                "E-002",
                "E-003",
                "E-004",
                "E-005",
                "T-901",
                "T-902",
                "T-903",
            ],
        ),
        "<body:verified_email_eq>:(true)": (
            {},
            '{"verified_email_eq": "true"}',
            12,
            10,
            [
                "D-001",
                "D-002",
                "D-005",
                "D-102",
                "D-103",
                "E-001",
                "E-002",
                "E-301",
                "E-302",
                "E-303",
            ],
        ),
        "<body:verified_email_eq>:(false)": (
            {},
            '{"verified_email_eq": "false"}',
            12,
            10,
            [
                "D-003",
                "D-004",
                "D-101",
                "D-104",
                "D-105",
                "E-003",
                "E-004",
                "E-005",
                "E-305",
                "T-000",
            ],
        ),
        "<body:account_type_in>:(ADMINISTRATOR,PROVISIONAL)": (
            {},
            '{"account_type_in": ["ADMINISTRATOR","PROVISIONAL"]}',
            9,
            9,
            [
                "D-001",
                "D-002",
                "D-005",
                "D-101",
                "D-102",
                "E-003",
                "E-302",
                "E-305",
                "T-901",
            ],
        ),
        "<body:is_active_eq>:(true)": (
            {},
            '{"is_active_eq": "true"}',
            18,
            10,
            [
                "D-001",
                "D-002",
                "D-004",
                "D-005",
                "D-102",
                "D-103",
                "D-104",
                "E-001",
                "E-002",
                "E-003",
            ],
        ),
        "<body:is_active_eq>:(false)": (
            {},
            '{"is_active_eq": "false"}',
            6,
            6,
            [
                "D-003",
                "D-101",
                "D-105",
                "E-004",
                "E-301",
                "T-903",
            ],
        ),
        "複合ケース": (
            {"sort": "-account_type"},
            '{"nickname_ex": true, "email_dm": "shogun.com" }',
            2,
            2,
            [
                "D-004",
                "D-002",
            ],
        ),
    }

    @pytest.mark.parametrize(
        "param", list(valid_params.values()), ids=list(valid_params.keys())
    )
    # 正常ケース
    async def test_ok(
        self,
        app: FastAPI,
        general_client: AsyncClient,
        import_profile: DataFrame,
        param: tuple[any, str, int, int, List[str]],
    ) -> None:
        res = await general_client.post(
            app.url_path_for("accounts:search-profile"), params=param[0], data=param[1]
        )
        assert res.status_code == HTTP_200_OK
        result = ProfilePublicList(**res.json())
        # 取得件数
        assert result.count == param[2]
        assert len(result.profiles) == param[3]
        ids = [profile.account_id for profile in result.profiles]
        assert ids == param[4]

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    # 異常ケース（アクティベーションエラー）
    async def test_ng_activation(
        self, app: FastAPI, non_active_client: AsyncClient
    ) -> None:
        res = await non_active_client.post(
            app.url_path_for("accounts:search-profile"), params={}, data="{}"
        )
        assert res.status_code == HTTP_401_UNAUTHORIZED

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    # 異常ケース（認可エラー）
    async def test_ng_permission(
        self, app: FastAPI, provisional_client: AsyncClient
    ) -> None:
        res = await provisional_client.post(
            app.url_path_for("accounts:search-profile"), params={}, data="{}"
        )
        assert res.status_code == HTTP_403_FORBIDDEN

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    # 異常ケースパラメータ
    invalid_params = {
        "<query:limit>:範囲外(2000)": (
            {"limit": 2000},
            "{}",
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<query:limit>:範囲外(-1)": (
            {"limit": -1},
            "{}",
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<query:limit>:型不正": (
            {"limit": "AAA"},
            "{}",
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<query:limit>:None": (
            {"limit": None},
            "{}",
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<query:offset>:範囲外(-1)": (
            {"offset": -1},
            "{}",
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<query:offset>:型不正": (
            {"offset": "AAA"},
            "{}",
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<query:offset>:None": (
            {"offset": None},
            "{}",
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<query:sort>:フォーマット不正(符号なし)": (
            {"sort": "account_id"},
            "{}",
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<query:sort>:フォーマット不正(カンマなし)": (
            {"sort": "+account_id-user_name"},
            "{}",
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<query:sort>:項目不正(存在しないカラム)": (
            {"sort": "+name"},
            "{}",
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:account_id_sw>:文字列長超過": (
            {},
            '{"account_id_sw":"T-0001"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:user_name_cn>:文字列長超過": (
            {},
            '{"user_name_cn":"000000000100000000020000000003"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:nickname_cn>:文字列長超過": (
            {},
            '{"nickname_cn":"000000000100000000020000000003"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:nickname_ex>:型不正": (
            {},
            '{"nickname_ex": "AAA"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:nickname>:同時指定不正([CONTAINS][EXIST])": (
            {},
            '{"nickname_cn": ["T-901","T-902"],"nickname_ex": true}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:verified_email_eq>:型不正": (
            {},
            '{"verified_email_eq": "AAA"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:account_type_in>:要素数不足": (
            {},
            '{"account_type_in": []}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:account_type_in>:型不正": (
            {},
            '{"account_type_in": "AAA"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:account_type_in>:型不正(要素)": (
            {},
            '{"account_type_in": ["ADMINISTRATOR","AAA"]}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:is_active_eq>:型不正": (
            {},
            '{"is_active_eq": "AAA"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body>:未定義フィールド": (
            {},
            '{"dummy":"dummy"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body>:None": (
            {},
            None,
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
    }

    @pytest.mark.parametrize(
        "param", list(invalid_params.values()), ids=list(invalid_params.keys())
    )
    # 異常ケース（バリデーションエラー）
    async def test_ng_validation(
        self,
        app: FastAPI,
        general_client: AsyncClient,
        param: tuple[any, str, int],
    ) -> None:
        res = await general_client.post(
            app.url_path_for("accounts:search-profile"), params=param[0], data=param[1]
        )
        assert res.status_code == param[2]

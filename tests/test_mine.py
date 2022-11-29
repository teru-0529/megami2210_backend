#!/usr/bin/python3
# test_authtoken.py

import jwt
import pytest
import pytest_asyncio
from fastapi import FastAPI, HTTPException
from httpx import AsyncClient
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.routing import NoMatchFound
from starlette.status import (
    HTTP_200_OK,
    HTTP_401_UNAUTHORIZED,
    HTTP_409_CONFLICT,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from app.api.schemas.accounts import (
    AccountCreate,
    PasswordChange,
    ProfileInDB,
    ProfileUpdate,
)
from app.core.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_ALGORITHM,
    JWT_AUDIENCE,
    SECRET_KEY,
)
from app.services import auth_service
from app.services.accounts import AccountService
from tests.conftest import assert_profile

pytestmark = pytest.mark.asyncio
is_regression = True


@pytest_asyncio.fixture
async def duplicate_dummy_profile(session: AsyncSession) -> ProfileInDB:
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


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


@pytest.mark.skipif(not is_regression, reason="not regression phase")
class TestRouteExists:
    async def test_login_route(self, app: FastAPI, client: AsyncClient) -> None:
        try:
            await client.post(app.url_path_for("mine:login"), data="{}")
        except NoMatchFound:
            pytest.fail("route not exist")

    async def test_get_my_profile_route(
        self, app: FastAPI, client: AsyncClient
    ) -> None:
        try:
            await client.get(app.url_path_for("mine:get-profile"))
        except NoMatchFound:
            pytest.fail("route not exist")

    async def test_patch_my_profile_route(
        self, app: FastAPI, client: AsyncClient
    ) -> None:
        try:
            await client.patch(app.url_path_for("mine:patch-profile"), data="{}")
        except NoMatchFound:
            pytest.fail("route not exist")

    async def test_password_change_route(
        self, app: FastAPI, client: AsyncClient
    ) -> None:
        try:
            await client.patch(app.url_path_for("mine:change-password"), data="{}")
        except NoMatchFound:
            pytest.fail("route not exist")


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


@pytest.mark.skipif(not is_regression, reason="not regression phase")
class TestCreateToken:

    # 正常ケース
    async def test_ok_case(self, fixed_account: ProfileInDB) -> None:

        token = auth_service.create_token_for_user(
            account=fixed_account,
            secret_key=str(SECRET_KEY),
            audience=JWT_AUDIENCE,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES,
        )
        print(token)
        creds = jwt.decode(
            token, str(SECRET_KEY), audience=JWT_AUDIENCE, algorithms=[JWT_ALGORITHM]
        )
        assert creds.get("sub") is not None
        assert creds["sub"] == fixed_account.account_id
        assert creds["aud"] == JWT_AUDIENCE

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    # 異常ケース(ユーザー無し)
    async def test_ng_case_none_account(self) -> None:
        token = auth_service.create_token_for_user(
            account=None,
            secret_key=str(SECRET_KEY),
            audience=JWT_AUDIENCE,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES,
        )
        with pytest.raises(jwt.PyJWTError):
            jwt.decode(
                token,
                str(SECRET_KEY),
                audience=JWT_AUDIENCE,
                algorithms=[JWT_ALGORITHM],
            )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    # 異常ケースパラメータ
    invalid_params = {
        "<secret-key>:不正": (
            "wrong-secret",
            JWT_AUDIENCE,
            jwt.InvalidSignatureError,
        ),
        "<secret-key>:None": (
            None,
            JWT_AUDIENCE,
            jwt.InvalidSignatureError,
        ),
        "<audience>:別サイト": (
            str(SECRET_KEY),
            "othersite-auth",
            jwt.InvalidAudienceError,
        ),
        "<audience>:None": (
            str(SECRET_KEY),
            None,
            ValidationError,
        ),
    }

    # 異常ケース(パラメータ不正)
    @pytest.mark.parametrize(
        "param", list(invalid_params.values()), ids=list(invalid_params.keys())
    )
    async def test_ng_case(
        self, fixed_account: ProfileInDB, param: tuple[str, str, BaseException]
    ) -> None:

        with pytest.raises(param[2]):
            token = auth_service.create_token_for_user(
                account=fixed_account,
                secret_key=str(param[0]),
                audience=param[1],
                expires_in=ACCESS_TOKEN_EXPIRE_MINUTES,
            )
            print(token)
            jwt.decode(
                token,
                str(SECRET_KEY),
                audience=JWT_AUDIENCE,
                algorithms=[JWT_ALGORITHM],
            )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


@pytest.mark.skipif(not is_regression, reason="not regression phase")
class TestLogin:

    # 正常ケース
    async def test_ok_case(
        self, app: FastAPI, client: AsyncClient, fixed_account: ProfileInDB
    ) -> None:
        client.headers["content-type"] = "application/x-www-form-urlencoded"
        login_data = {
            "username": fixed_account.account_id,
            "password": fixed_account.init_password,
        }
        res = await client.post(app.url_path_for("mine:login"), data=login_data)
        assert res.status_code == HTTP_200_OK

        access_token = res.json()
        assert "access_token" in access_token
        assert "token_type" in access_token

        assert access_token.get("token_type") == "bearer"
        token = access_token.get("access_token")
        creds = jwt.decode(
            token, str(SECRET_KEY), audience=JWT_AUDIENCE, algorithms=[JWT_ALGORITHM]
        )
        assert "sub" in creds
        assert creds["sub"] == fixed_account.account_id

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    # 異常ケースパラメータ
    invalid_params = {
        "<username>:不正": (
            "account_id",
            "wrong-account-id",
            HTTP_401_UNAUTHORIZED,
        ),
        "<username>:None": (
            "account_id",
            None,
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<password>:不正": (
            "init_password",
            "wrong-password",
            HTTP_401_UNAUTHORIZED,
        ),
        "<password>:None": (
            "init_password",
            None,
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
    }

    @pytest.mark.parametrize(
        "param", list(invalid_params.values()), ids=list(invalid_params.keys())
    )
    # 異常ケース
    async def test_ng_case(
        self,
        app: FastAPI,
        client: AsyncClient,
        fixed_account: ProfileInDB,
        param: tuple[str, str, int],
    ) -> None:
        client.headers["content-type"] = "application/x-www-form-urlencoded"
        dict = fixed_account.dict()
        dict[param[0]] = param[1]
        login_data = {
            "username": dict["account_id"],
            "password": dict["init_password"],
        }
        res = await client.post(app.url_path_for("mine:login"), data=login_data)
        assert res.status_code == param[2]
        assert "access_token" not in res.json()


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


@pytest.mark.skipif(not is_regression, reason="not regression phase")
class TestGetIdFromToken:

    # 正常ケース
    async def test_ok_case(self, fixed_account: ProfileInDB) -> None:
        token = auth_service.create_token_for_user(
            account=fixed_account, secret_key=str(SECRET_KEY)
        )
        account_id = auth_service.get_id_from_token(
            token=token, secret_key=str(SECRET_KEY)
        )
        assert account_id == fixed_account.account_id

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    # 異常ケースパラメータ
    invalid_params = {
        "<token>:不正": (
            SECRET_KEY,
            "dummy token",
        ),
        "<token>:brank": (
            SECRET_KEY,
            "",
        ),
        "<token>:None": (
            SECRET_KEY,
            None,
        ),
        "<secret_key>:不正": (
            "abc123def",
            "use correct token",
        ),
    }

    @pytest.mark.parametrize(
        "param", list(invalid_params.values()), ids=list(invalid_params.keys())
    )
    # 異常ケース
    async def test_ng_case(
        self,
        fixed_account: ProfileInDB,
        param: tuple[str, str],
    ) -> None:
        token = auth_service.create_token_for_user(
            account=fixed_account, secret_key=str(SECRET_KEY)
        )
        if param[1] != "use correct token":
            token = param[1]

        with pytest.raises(HTTPException):
            auth_service.get_id_from_token(token=token, secret_key=str(param[0]))


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


@pytest.mark.skipif(not is_regression, reason="not regression phase")
class TestGetMyProfile:

    # 正常ケース
    async def test_ok_case(
        self, app: FastAPI, authorized_client: AsyncClient, fixed_account: ProfileInDB
    ) -> None:
        res = await authorized_client.get(app.url_path_for("mine:get-profile"))
        assert res.status_code == HTTP_200_OK

        my_account = ProfileInDB(**res.json())
        assert_profile(actual=my_account, expected=fixed_account)

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    # 異常ケース（未認証クライアント）
    async def test_ng_case_unauthorized(
        self, app: FastAPI, client: AsyncClient
    ) -> None:
        res = await client.get(app.url_path_for("mine:get-profile"))
        assert res.status_code == HTTP_401_UNAUTHORIZED

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    # 異常ケースパラメータ
    invalid_params = {
        "<jwt_prefix>:brank": "",
        "<jwt_prefix>:Token": "Token",
        "<jwt_prefix>:JWT": "JWT",
    }

    @pytest.mark.parametrize(
        "jwt_prefix", list(invalid_params.values()), ids=list(invalid_params.keys())
    )
    # 異常ケース
    async def test_ng_case(
        self,
        app: FastAPI,
        client: AsyncClient,
        fixed_account: ProfileInDB,
        jwt_prefix: str,
    ) -> None:
        token = auth_service.create_token_for_user(account=fixed_account)
        res = await client.get(
            app.url_path_for("mine:get-profile"),
            headers={"Authorization": f"{jwt_prefix} {token}"},
        )
        assert res.status_code == HTTP_401_UNAUTHORIZED


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


@pytest.mark.skipif(not is_regression, reason="not regression phase")
class TestPatchProfile:
    # 正常ケースパラメータ
    valid_params = {
        "<body:nickname>": ProfileUpdate(nickname="将軍"),
        "<body:email>": ProfileUpdate(email="shogun@edobakufu.com"),
        "複合ケース": ProfileUpdate(nickname="東証大権現", email="daigongen@nikko.com"),
    }

    @pytest.mark.parametrize(
        "update_params", list(valid_params.values()), ids=list(valid_params.keys())
    )
    async def test_ok_case(
        self,
        app: FastAPI,
        authorized_client: AsyncClient,
        fixed_account: ProfileInDB,
        update_params: ProfileUpdate,
    ) -> None:
        res = await authorized_client.patch(
            app.url_path_for("mine:patch-profile"),
            data=update_params.json(exclude_unset=True),
        )
        assert res.status_code == HTTP_200_OK
        updated_profile = ProfileInDB(**res.json())

        update_dict = update_params.dict(exclude_unset=True)
        expected_profile = fixed_account.copy(update=update_dict)

        assert_profile(actual=updated_profile, expected=expected_profile)

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    # 異常ケース（未認証クライアント）
    async def test_ng_case_unauthorized(
        self, app: FastAPI, client: AsyncClient
    ) -> None:
        res = await client.patch(app.url_path_for("mine:patch-profile"), data="{}")
        assert res.status_code == HTTP_401_UNAUTHORIZED

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    # 異常ケースパラメータ
    invalid_params = {
        "<body:nickname>:桁数超過": (
            '{"nickname":"000000000100000000020000000003"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:email>:フォーマット不正①": (
            '{"email":"shingen.sengoku"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:email>:フォーマット不正②": (
            '{"email":"sengoku.com"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:email>:フォーマット不正③": (
            '{"email":"shingen@takeda@com"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:email>:None": (
            '{"email":null}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body>:変更不可フィールド(account_type)": (
            '{"account_type":"GENERAL"}',
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
        authorized_client: AsyncClient,
        param: tuple[str, int],
    ) -> None:
        res = await authorized_client.patch(
            app.url_path_for("mine:patch-profile"), data=param[0]
        )
        assert res.status_code == param[1]

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    # 異常(DB相関)ケースパラメータ
    invalid_db_params = {
        "duplicate:[email]": (
            '{"email":"tokugawa@sengoku.com"}',
            HTTP_409_CONFLICT,
        ),
    }

    @pytest.mark.parametrize(
        "param", list(invalid_db_params.values()), ids=list(invalid_db_params.keys())
    )
    async def test_db_ng_case(
        self,
        app: FastAPI,
        authorized_client: AsyncClient,
        param: tuple[str, int],
        duplicate_dummy_profile: ProfileInDB,
    ) -> None:
        res = await authorized_client.patch(
            app.url_path_for("mine:patch-profile"), data=param[0]
        )
        assert res.status_code == param[1]


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


@pytest.mark.skipif(not is_regression, reason="not regression phase")
class TestChangePassword:
    # 正常ケース
    async def test_ok_case(
        self,
        app: FastAPI,
        authorized_client: AsyncClient,
        fixed_account: ProfileInDB,
    ) -> None:
        update_param = PasswordChange(new_password="new_password")

        login_data = {
            "username": fixed_account.account_id,
            "password": update_param.new_password,
        }

        # 変更前は新パスワードでログインできないこと
        authorized_client.headers["content-type"] = "application/x-www-form-urlencoded"
        res = await authorized_client.post(
            app.url_path_for("mine:login"), data=login_data
        )
        assert res.status_code == HTTP_401_UNAUTHORIZED

        authorized_client.headers["content-type"] = ""
        res = await authorized_client.patch(
            app.url_path_for("mine:change-password"),
            data=update_param.json(exclude_unset=True),
        )
        assert res.status_code == HTTP_200_OK

        # 変更後は新パスワードでログインできること
        authorized_client.headers["content-type"] = "application/x-www-form-urlencoded"
        res = await authorized_client.post(
            app.url_path_for("mine:login"), data=login_data
        )
        assert res.status_code == HTTP_200_OK

        # 変更後のアカウントがアクティベート状態であること
        authorized_client.headers["content-type"] = ""
        res = await authorized_client.get(app.url_path_for("mine:get-profile"))
        assert res.status_code == HTTP_200_OK
        profile = ProfileInDB(**res.json())
        profile.is_active is True

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    # 異常ケース（未認証クライアント）
    async def test_ng_case_unauthorized(
        self, app: FastAPI, client: AsyncClient
    ) -> None:
        res = await client.patch(app.url_path_for("mine:change-password"), data="{}")
        assert res.status_code == HTTP_401_UNAUTHORIZED

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    # 異常ケースパラメータ
    invalid_params = {
        "<body:new_password>:桁数不足": (
            '{"new_password":"pass"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:new_password>:None": (
            '{"new_password":None}',
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
        authorized_client: AsyncClient,
        param: tuple[str, int],
    ) -> None:
        res = await authorized_client.patch(
            app.url_path_for("mine:change-password"), data=param[0]
        )
        assert res.status_code == param[1]

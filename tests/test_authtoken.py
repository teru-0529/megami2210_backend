#!/usr/bin/python3
# test_authtoken.py

import jwt
import pytest
from fastapi import FastAPI, HTTPException
from httpx import AsyncClient
from pydantic import ValidationError
from starlette.routing import NoMatchFound
from starlette.status import (
    HTTP_200_OK,
    HTTP_401_UNAUTHORIZED,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from app.api.schemas.accounts import ProfileInDB
from app.core.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_ALGORITHM,
    JWT_AUDIENCE,
    SECRET_KEY,
)
from app.services import auth_service
from tests.conftest import assert_profile

pytestmark = pytest.mark.asyncio
is_regression = True

# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


@pytest.mark.skipif(not is_regression, reason="not regression phase")
class TestRouteExists:
    async def test_login_route(self, app: FastAPI, client: AsyncClient) -> None:
        try:
            await client.post(app.url_path_for("mine:login"), data="{}")
        except NoMatchFound:
            pytest.fail("route not exist")

    async def test_get_mine_route(self, app: FastAPI, client: AsyncClient) -> None:
        try:
            await client.get(app.url_path_for("mine:get"))
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
class TestGetMine:

    # 正常ケース
    async def test_ok_case(
        self, app: FastAPI, authorized_client: AsyncClient, fixed_account: ProfileInDB
    ) -> None:
        res = await authorized_client.get(app.url_path_for("mine:get"))
        assert res.status_code == HTTP_200_OK

        my_account = ProfileInDB(**res.json())
        assert_profile(actual=my_account, expected=fixed_account)

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    # 異常ケース（未認証クライアント）
    async def test_ng_case_unauthorized(
        self, app: FastAPI, client: AsyncClient
    ) -> None:
        res = await client.get(app.url_path_for("mine:get"))
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
            app.url_path_for("mine:get"),
            headers={"Authorization": f"{jwt_prefix} {token}"},
        )
        assert res.status_code == HTTP_401_UNAUTHORIZED

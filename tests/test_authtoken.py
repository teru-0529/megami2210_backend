#!/usr/bin/python3
# test_authtoken.py

import jwt
import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from pydantic import ValidationError

from app.api.schemas.accounts import ProfileInDB
from app.core.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_ALGORITHM,
    JWT_AUDIENCE,
    SECRET_KEY,
)
from app.services import auth_service

# pytestmark = pytest.mark.asyncio
is_regression = True


@pytest.fixture
def fake_account() -> ProfileInDB:
    return ProfileInDB(
        account_id="T-000",
        user_name="織田信長",
        nickname="魔王",
        email="oda@sengoku.com",
        account_type="GENERAL",
        is_active=True,
        verified_email=True,
        init_password="testPassword",
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


@pytest.mark.skipif(not is_regression, reason="not regression phase")
class TestCreateToken:

    # 正常ケース
    @pytest.mark.asyncio
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
    def test_ng_case_none_account(self) -> None:
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
    @pytest.mark.asyncio
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
    @pytest.mark.asyncio
    async def test_ok_case(
        self, app: FastAPI, client: AsyncClient, fixed_account: ProfileInDB
    ) -> None:
        pass
        # token = auth_service.create_token_for_user(
        #     account=fake_account,
        #     secret_key=str(SECRET_KEY),
        #     audience=JWT_AUDIENCE,
        #     expires_in=ACCESS_TOKEN_EXPIRE_MINUTES,
        # )
        # print(token)
        # creds = jwt.decode(
        #     token, str(SECRET_KEY), audience=JWT_AUDIENCE, algorithms=[JWT_ALGORITHM]
        # )
        # assert creds.get("sub") is not None
        # assert creds["sub"] == fake_account.account_id
        # assert creds["aud"] == JWT_AUDIENCE

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

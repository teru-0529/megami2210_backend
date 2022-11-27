#!/usr/bin/python3
# authentication.py

import random
import string
from datetime import datetime, timedelta
from typing import Tuple

import bcrypt
import jwt
from fastapi import HTTPException
from pydantic import ValidationError
from starlette.status import HTTP_401_UNAUTHORIZED

from app.api.schemas.accounts import ProfileInDB
from app.api.schemas.token import JWTCreds, JWTMeta, JWTPayload
from app.core.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_ALGORITHM,
    JWT_AUDIENCE,
    SECRET_KEY,
)

# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----


class AuthError(BaseException):
    pass


class AuthService:
    def generate_init_password(self, length: int = 20) -> str:
        """初期パスワードの生成"""
        randlst = [
            random.choice(string.ascii_letters + string.digits) for i in range(length)
        ]
        return "".join(randlst)

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    def create_hash_password(self, plaintext_password: str) -> Tuple[str, str]:
        """solt生成/パスワードのhash、authモデルに設定する"""
        solt: str = self._generate_solt()
        hashed_password = self._hash_password(plaintext_password, solt)
        return hashed_password, solt

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    def check_password(self, plaintext_password: str, hash_password: str) -> bool:
        """パスワードのチェックをする"""
        return bcrypt.checkpw(
            password=plaintext_password.encode(), hashed_password=hash_password.encode()
        )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    def create_token_for_user(
        self,
        *,
        account: ProfileInDB,
        secret_key: str = str(SECRET_KEY),
        audience: str = JWT_AUDIENCE,
        expires_in: int = ACCESS_TOKEN_EXPIRE_MINUTES
    ) -> str:
        """JWTを作成する"""
        if not account or not isinstance(account, ProfileInDB):
            return None
        jwt_meta = JWTMeta(
            aud=audience,
            iat=datetime.timestamp(datetime.utcnow()),
            exp=datetime.timestamp(datetime.utcnow() + timedelta(minutes=expires_in)),
        )
        jwt_creds = JWTCreds(sub=account.account_id)
        payload = JWTPayload(**jwt_meta.dict(), **jwt_creds.dict())
        token = jwt.encode(
            payload=payload.dict(), key=secret_key, algorithm=JWT_ALGORITHM
        )
        return token

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    def get_id_from_token(
        self, *, token: str, secret_key: str = str(SECRET_KEY)
    ) -> str:
        """JWTからログイン中のアカウントを再現する"""
        try:
            decoded_token = jwt.decode(
                token, key=secret_key, audience=JWT_AUDIENCE, algorithms=JWT_ALGORITHM
            )
            payload = JWTPayload(**decoded_token)
        except (jwt.PyJWTError, ValidationError):
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Could not validate token credentials.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload.sub

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----
    # [INNER] soltの生成
    def _generate_solt(self) -> str:
        return bcrypt.gensalt(prefix=b"2a").decode()

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----
    # [INNER] パスワードのHash化
    def _hash_password(self, password: str, solt: str) -> str:
        return bcrypt.hashpw(password=password.encode(), salt=solt.encode()).decode()

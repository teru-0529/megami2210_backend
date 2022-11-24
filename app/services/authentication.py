#!/usr/bin/python3
# authentication.py

import random
import string
from typing import Tuple

import bcrypt

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
        # auth.password = hashed_password
        # auth.solt = solt
        return hashed_password, solt

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    def check_password(self, plaintext_password: str, hash_password: str) -> bool:
        """パスワードのチェックをする"""
        return bcrypt.checkpw(
            password=plaintext_password.encode(), hashed_password=hash_password.encode()
        )
        # solt: str = self._generate_solt()
        # hashed_password = self._hash_password(plaintext_password, solt)
        # auth.password = hashed_password
        # auth.solt = solt
        # return {"password": hashed_password, "solt": solt}

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----
    # [INNER] soltの生成
    def _generate_solt(self) -> str:
        return bcrypt.gensalt(prefix=b"2a").decode()

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----
    # [INNER] パスワードのHash化
    def _hash_password(self, password: str, solt: str) -> str:
        return bcrypt.hashpw(password=password.encode(), salt=solt.encode()).decode()

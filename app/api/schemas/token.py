#!/usr/bin/python3
# token.py

from datetime import timedelta, datetime
from app.core.config import JWT_AUDIENCE, ACCESS_TOKEN_EXPIRE_MINUTES
from app.api.schemas.base import CoreModel

# from pydantic import EmailStr
# from app.api.schemas.accounts import f_account_id


class JWTMeta(CoreModel):
    iss: str = "megumi2210.com"
    aud: str = JWT_AUDIENCE
    iat: float = datetime.timestamp(datetime.utcnow())
    exp: float = datetime.timestamp(
        datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )


class JWTCreds(CoreModel):
    sub: str
    # account_id: str = f_account_id


class JWTPayload(JWTMeta, JWTCreds):
    pass


class AccessToken(CoreModel):
    access_token: str
    token_type: str

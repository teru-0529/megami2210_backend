#!/usr/bin/python3
# token.py

from datetime import timedelta, datetime
from app.core.config import JWT_AUDIENCE, ACCESS_TOKEN_EXPIRE_MINUTES
from app.api.schemas.base import CoreModel


class JWTMeta(CoreModel):
    iss: str = "megumi2210.com"
    aud: str = JWT_AUDIENCE
    iat: float = datetime.timestamp(datetime.utcnow())
    exp: float = datetime.timestamp(
        datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )


class JWTCreds(CoreModel):
    sub: str


class JWTPayload(JWTMeta, JWTCreds):
    pass


class AccessToken(CoreModel):
    access_token: str
    token_type: str

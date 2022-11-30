#!/usr/bin/python3
# token.py

from datetime import datetime, timedelta

from pydantic import Field

from app.api.schemas.base import CoreModel
from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES, JWT_AUDIENCE


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
    access_token: str = Field(
        title="AccessToken", description="アクセストークン", example="token"
    )
    token_type: str = Field(title="TokenType", description="トークン種類", example="bearer")

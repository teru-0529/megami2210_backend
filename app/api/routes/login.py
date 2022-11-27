#!/usr/bin/python3
# login.py

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.accounts import ProfileInDB
from app.api.schemas.base import Message
from app.api.schemas.token import AccessToken
from app.core.config import API_PREFIX
from app.core.database import get_session
from app.services.accounts import AccountService

router = APIRouter()

# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{API_PREFIX}/login/")


@router.post(
    "/login",
    name="mine:login",
    responses={
        401: {
            "model": Message,
            "description": "Auth error",
            "content": {
                "application/json": {
                    "example": {"detail": "Authentication was unsuccessful."}
                }
            },
        },
        200: {"model": AccessToken, "description": "login successfull"},
    },
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(OAuth2PasswordRequestForm),
    session: AsyncSession = Depends(get_session),
) -> AccessToken:
    """
    システムへのログイン。</br>

    [FORM]

    - **username**: アカウントID[reqired]
    - **password**: パスワード[reqired]

    上記以外は利用しない。
    """

    service = AccountService()
    access_token = await service.login(
        session=session, id=form_data.username, password=form_data.password
    )
    return access_token


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


@router.get(
    "/mine",
    name="mine:get",
    responses={
        401: {
            "model": Message,
            "description": "Auth error",
            "content": {
                "application/json": {
                    "example": {"detail": "Authentication was unsuccessful."}
                }
            },
        },
        200: {"model": ProfileInDB, "description": "My account"},
    },
)
async def get_my_account(
    session: AsyncSession = Depends(get_session),
    token: str = Depends(oauth2_scheme),
) -> ProfileInDB:
    """
    ログイン中のアカウント情報を入手する。</br>

    """
    service = AccountService()
    profile = await service.get_mine(session=session, token=token)
    return profile

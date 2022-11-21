#!/usr/bin/python3
# accouts.py

from fastapi import APIRouter, Body, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_200_OK

from app.api.schemas.accounts import UserCreate, UserPublic, p_account_id
from app.api.schemas.base import Message
from app.core.database import get_session
from app.services.accounts import AccountService

router = APIRouter()


@router.put(
    "/{id}/",
    response_model=UserPublic,
    name="accounts:create",
    status_code=HTTP_200_OK,
    responses={
        400: {
            "model": Message,
            "description": "The task was not found",
            "content": {
                "application/json": {
                    "example": {"detail": "duplicate key: [account_id]."}
                }
            },
        },
        200: {"model": UserPublic, "description": "New account created"},
    },
)
async def create_task(
    id: str = p_account_id,
    new_account: UserCreate = Body(...),
    session: AsyncSession = Depends(get_session),
) -> UserPublic:
    """
    アカウントの新規作成。</br>

    [PATH]

    - **id**: アカウントID[reqired]

    [BODY]

    - **user_name**: ユーザー氏名[reqired]
    - **email**: Eメールアドレス[reqired]
    - **account_type**: アカウント種類[default=GENERAL]
    """

    service = AccountService()
    created_account = await service.create(
        session=session, id=id, new_account=new_account
    )
    return created_account


@router.get(
    "/{id}/",
    response_model=UserPublic,
    name="accounts:get-by-id",
    status_code=HTTP_200_OK,
    responses={
        404: {
            "model": Message,
            "description": "The user was not found",
            "content": {
                "application/json": {"example": {"detail": "Resource not found."}}
            },
        },
        200: {"model": UserPublic, "description": "User requested by ID"},
    },
)
async def get_user_by_id(
    id: str = p_account_id,
    session: AsyncSession = Depends(get_session),
) -> UserPublic:
    """
    アカウント1件の取得。</br>

    [PATH]

    - **id**: アカウントID[reqired]
    """
    service = AccountService()
    account = await service.get_by_id(session=session, id=id)
    return account

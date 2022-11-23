#!/usr/bin/python3
# accouts.py

from fastapi import APIRouter, Body, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_200_OK

from app.api.schemas.accounts import (
    UserCreate,
    UserPublic,
    p_account_id,
    UserProfileUpdate,
    UserBaseProfileUpdate,
)
from app.api.schemas.base import Message
from app.core.database import get_session
from app.services.accounts import AccountService

router = APIRouter()

# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


@router.put(
    "/{id}/",
    name="accounts:create",
    status_code=HTTP_200_OK,
    responses={
        400: {
            "model": Message,
            "description": "Wrong input parameters",
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


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


@router.get(
    "/{id}/",
    name="accounts:get-by-id",
    status_code=HTTP_200_OK,
    responses={
        404: {
            "model": Message,
            "description": "The account was not found",
            "content": {
                "application/json": {"example": {"detail": "Resource not found."}}
            },
        },
        200: {"model": UserPublic, "description": "Account requested by ID"},
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


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


@router.patch(
    "/{id}/profile",
    name="accounts:patch-profile",
    status_code=HTTP_200_OK,
    responses={
        404: {
            "model": Message,
            "description": "The account was not found",
            "content": {
                "application/json": {"example": {"detail": "Resource not found."}}
            },
        },
        200: {"model": UserPublic, "description": "Account profile patched by ID"},
    },
)
async def patch_account_profile(  # FIXME:将来的にはログインユーザーの変更
    id: str = p_account_id,
    patch_params: UserProfileUpdate = Body(...),
    session: AsyncSession = Depends(get_session),
) -> UserPublic:
    """
    本人によるアカウント1件の更新。</br>
    **user_name**、**account_type** は管理者管轄項目のため変更不可、**password** の変更は別APIで実施。:

    [PATH]

    - **id**: アカウントID[reqired]

    [BODY]

    - **nickname**: ニックネーム
    - **email**: Eメールアドレス[not-nullable]
    """
    service = AccountService()
    account = await service.patch_profile(
        session=session, id=id, patch_params=patch_params
    )
    return account


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


@router.patch(
    "/{id}/base-profile",
    name="accounts:patch-base-profile",
    status_code=HTTP_200_OK,
    responses={
        404: {
            "model": Message,
            "description": "The account was not found",
            "content": {
                "application/json": {"example": {"detail": "Resource not found."}}
            },
        },
        200: {"model": UserPublic, "description": "Account profile patched by ID"},
    },
)
async def patch_account_base_profile(
    id: str = p_account_id,
    patch_params: UserBaseProfileUpdate = Body(...),
    session: AsyncSession = Depends(get_session),
) -> UserPublic:
    """
    管理者によるアカウント1件の更新。</br>
    **nickname**、**email** は本人管轄項目のため変更不可。:

    [PATH]

    - **id**: アカウントID[reqired]

    [BODY]

    - **user_name**: ユーザー氏名[not-nullable]
    - **account_type**: アカウント種別[not-nullable]
    """
    service = AccountService()
    account = await service.patch_base_profile(
        session=session, id=id, patch_params=patch_params
    )
    return account


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


@router.delete(
    "/{id}/",
    name="accounts:delete",
    status_code=HTTP_200_OK,
    responses={
        404: {
            "model": Message,
            "description": "The account was not found",
            "content": {
                "application/json": {"example": {"detail": "Resource not found."}}
            },
        },
        200: {"model": UserPublic, "description": "Account deleted by ID"},
    },
)
async def delete_account(
    id: str = p_account_id,
    session: AsyncSession = Depends(get_session),
) -> UserPublic:
    """
    アカウント1件の削除。

    [PATH]

    - **id**: アカウントID[reqired]

    """
    service = AccountService()
    account = await service.delete(session=session, id=id)
    return account

#!/usr/bin/python3
# accouts.py

from fastapi import APIRouter, Body, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.accounts import (
    AccountCreate,
    InitPass,
    PasswordChange,
    PasswordReset,
    ProfileBaseUpdate,
    ProfilePublic,
    ProfilePublicWithInitPass,
    ProfileUpdate,
    p_account_id,
)
from app.api.schemas.base import Message
from app.core.database import get_session
from app.services.accounts import AccountService

router = APIRouter()

# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


@router.put(
    "/{id}/",
    name="accounts:create",
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
        200: {"model": ProfilePublicWithInitPass, "description": "New account created"},
    },
)
async def create(
    id: str = p_account_id,
    new_account: AccountCreate = Body(...),
    session: AsyncSession = Depends(get_session),
) -> ProfilePublicWithInitPass:
    """
    アカウントの新規作成。</br>
    作成したアカウントは非Active状態。発行した初期パスワードを変更することでアクティベートされる。

    [PATH]

    - **id**: アカウントID[reqired]

    [BODY]

    - **user_name**: ユーザー氏名[reqired]
    - **email**: Eメールアドレス[reqired]
    - **account_type**: アカウント種類[default=GENERAL]
    - **init_password**: 初期パスワード ※未設定の場合は内部でランダムに生成する
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
    responses={
        404: {
            "model": Message,
            "description": "The account was not found",
            "content": {
                "application/json": {"example": {"detail": "Resource not found."}}
            },
        },
        200: {"model": ProfilePublic, "description": "Account requested by ID"},
    },
)
async def get_by_id(
    id: str = p_account_id,
    session: AsyncSession = Depends(get_session),
) -> ProfilePublic:
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
    responses={
        400: {
            "model": Message,
            "description": "Wrong input parameters",
            "content": {
                "application/json": {"example": {"detail": "duplicate key: [email]."}}
            },
        },
        404: {
            "model": Message,
            "description": "The account was not found",
            "content": {
                "application/json": {"example": {"detail": "Resource not found."}}
            },
        },
        200: {"model": ProfilePublic, "description": "Account profile patched by ID"},
    },
)
async def patch_profile(  # FIXME:将来的にはログインユーザーの変更
    id: str = p_account_id,
    patch_params: ProfileUpdate = Body(...),
    session: AsyncSession = Depends(get_session),
) -> ProfilePublic:
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
    responses={
        400: {
            "model": Message,
            "description": "Wrong input parameters",
            "content": {
                "application/json": {
                    "example": {"detail": "duplicate key: [user_name]."}
                }
            },
        },
        404: {
            "model": Message,
            "description": "The account was not found",
            "content": {
                "application/json": {"example": {"detail": "Resource not found."}}
            },
        },
        200: {"model": ProfilePublic, "description": "Account profile patched by ID"},
    },
)
async def patch_base_profile(
    id: str = p_account_id,
    patch_params: ProfileBaseUpdate = Body(...),
    session: AsyncSession = Depends(get_session),
) -> ProfilePublic:
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
    responses={
        404: {
            "model": Message,
            "description": "The account was not found",
            "content": {
                "application/json": {"example": {"detail": "Resource not found."}}
            },
        },
        200: {"model": ProfilePublic, "description": "Account deleted by ID"},
    },
)
async def delete(
    id: str = p_account_id,
    session: AsyncSession = Depends(get_session),
) -> ProfilePublic:
    """
    アカウント1件の削除。

    [PATH]

    - **id**: アカウントID[reqired]

    """
    service = AccountService()
    account = await service.delete(session=session, id=id)
    return account


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


@router.patch(
    "/{id}/password",
    name="accounts:password-change",
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
        404: {
            "model": Message,
            "description": "The account was not found",
            "content": {
                "application/json": {"example": {"detail": "Resource not found."}}
            },
        },
        200: {"model": None, "description": "Password changed"},
    },
)
async def change_password(
    id: str = p_account_id,
    pass_change: PasswordChange = Body(...),
    session: AsyncSession = Depends(get_session),
) -> None:
    """
    パスワードの変更。</br>
    変更することでアカウントはActive状態になる。

    [PATH]

    - **id**: アカウントID[reqired]

    [BODY]

    - **old_password**: 現パスワード[reqired]
    - **new_password**: 新パスワード[reqired]
    """

    service = AccountService()
    await service.password_change(session=session, id=id, pass_change=pass_change)


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


@router.put(
    "/{id}/password",
    name="accounts:password-reset",
    responses={
        404: {
            "model": Message,
            "description": "The account was not found",
            "content": {
                "application/json": {"example": {"detail": "Resource not found."}}
            },
        },
        200: {"model": InitPass, "description": "Password reseted"},
    },
)
async def reset_password(
    id: str = p_account_id,
    pass_reset: PasswordReset = Body(...),
    session: AsyncSession = Depends(get_session),
) -> InitPass:
    """
    パスワードのリセット。</br>
    アカウントを非Active化し初期パスワード再発行する。変更することでアカウントが再度アクティベートされる。

    [PATH]

    - **id**: アカウントID[reqired]

    [BODY]

    - **init_password**: 初期パスワード ※未設定の場合は内部でランダムに生成する
    """

    service = AccountService()
    init_pass = await service.password_reset(
        session=session, id=id, pass_reset=pass_reset
    )
    return init_pass

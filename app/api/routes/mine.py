#!/usr/bin/python3
# login.py

from typing import List

from fastapi import APIRouter, Body, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.accounts import PasswordChange, ProfilePublic, ProfileUpdate
from app.api.schemas.base import Message
from app.api.schemas.tasks import TaskWithWatchNote, WatchTask, p_task_id
from app.api.schemas.token import AccessToken
from app.core.config import API_PREFIX
from app.core.database import get_session
from app.services.accounts import AccountService
from app.services.permittion import CkPermission

router = APIRouter()

# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{API_PREFIX}/login/")


@router.post(
    "/login",
    name="mine:login",
    responses={
        401: {
            "model": Message,
            "description": "Auth Error",
            "content": {
                "application/json": {
                    "example": {"detail": "Authentication was unsuccessful."}
                }
            },
        },
        200: {"model": AccessToken, "description": "Login successfull"},
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
    "/mine/profile",
    name="mine:get-profile",
    responses={
        401: {
            "model": Message,
            "description": "Auth Error",
            "content": {
                "application/json": {
                    "example": {"detail": "Authentication was unsuccessful."}
                }
            },
        },
        200: {"model": ProfilePublic, "description": "Get profile successful"},
    },
)
async def get_profile(
    session: AsyncSession = Depends(get_session),
    token: str = Depends(oauth2_scheme),
) -> ProfilePublic:
    """
    ログイン中のアカウント情報を入手する。</br>
    すべてのユーザーが、アクティベート前でも実行可能。

    """
    service = AccountService()
    profile = await service.get_my_profile(session=session, token=token)
    return profile


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


@router.patch(
    "/mine/profile",
    name="mine:patch-profile",
    responses={
        409: {
            "model": Message,
            "description": "Resource conflict Error",
            "content": {
                "application/json": {"example": {"detail": "duplicate key: [email]."}}
            },
        },
        401: {
            "model": Message,
            "description": "Auth Error",
            "content": {
                "application/json": {
                    "example": {"detail": "Authentication was unsuccessful."}
                }
            },
        },
        200: {"model": ProfilePublic, "description": "Update profile successful"},
    },
)
async def patch_profile(
    patch_params: ProfileUpdate = Body(...),
    session: AsyncSession = Depends(get_session),
    token: str = Depends(oauth2_scheme),
) -> ProfilePublic:
    """
    ログイン中のアカウントの更新。</br>
    すべてのユーザーが、アクティベート前でも実行可能。</br>
    **user_name**、**account_type** は管理者管轄項目のため変更できない。**password** の変更は別APIで実施する。

    [BODY]

    - **nickname**: ニックネーム
    - **email**: Eメールアドレス[not-nullable]
    """
    service = AccountService()
    account = await service.patch_my_profile(
        session=session, token=token, patch_params=patch_params
    )
    return account


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


@router.patch(
    "/mine/password",
    name="mine:change-password",
    responses={
        401: {
            "model": Message,
            "description": "Auth Error",
            "content": {
                "application/json": {
                    "example": {"detail": "Authentication was unsuccessful."}
                }
            },
        },
        200: {
            "model": Message,
            "description": "Change password successful",
            "content": {
                "application/json": {
                    "example": {"detail": "Change password successful."}
                }
            },
        },
    },
)
async def change_password(
    pass_change: PasswordChange = Body(...),
    session: AsyncSession = Depends(get_session),
    token: str = Depends(oauth2_scheme),
) -> Message:
    """
    パスワードの変更。</br>
    変更することでアカウントはActive状態になる。</br>
    すべてのユーザーが実行可能。


    [BODY]

    - **new_password**: 新パスワード[reqired]
    """

    service = AccountService()
    await service.change_my_password(
        session=session, token=token, pass_change=pass_change
    )
    return {"detail": "Change password successful."}


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


@router.get(
    "/mine/watch-tasks/",
    name="mine:get-watch-tasks",
    responses={
        401: {
            "model": Message,
            "description": "Auth Error",
            "content": {
                "application/json": {
                    "example": {"detail": "Authentication was unsuccessful."}
                }
            },
        },
        200: {
            "model": List[TaskWithWatchNote],
            "description": "Get watch-tasks successful",
        },
    },
)
async def get_watch_tasks(
    session: AsyncSession = Depends(get_session),
    token: str = Depends(oauth2_scheme),
) -> List[TaskWithWatchNote]:
    """
    監視タスクの一覧を取得する。</br>
    アクティベート後のすべてのユーザーが実行可能。

    """
    checker = CkPermission(session=session, token=token)
    await checker.activate_only()

    service = AccountService()
    result = await service.get_watch_tasks(session=session, token=token)
    return result


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


@router.put(
    "/mine/watch-tasks/{id}/",
    name="mine:put-watch-task",
    responses={
        401: {
            "model": Message,
            "description": "Auth Error",
            "content": {
                "application/json": {
                    "example": {"detail": "Authentication was unsuccessful."}
                }
            },
        },
        404: {
            "model": Message,
            "description": "Resource not found Error",
            "content": {
                "application/json": {"example": {"detail": "Resource not found."}}
            },
        },
        200: {
            "model": Message,
            "description": "Set watch-task successful",
            "content": {
                "application/json": {
                    "example": {"detail": "Set watch-task successful."}
                }
            },
        },
    },
)
async def put_watch_task(
    id: int = p_task_id,
    watch_task: WatchTask = Body(...),
    session: AsyncSession = Depends(get_session),
    token: str = Depends(oauth2_scheme),
) -> Message:
    """
    監視タスクの登録。登録済みの場合は**note**を更新する。</br>
    アクティベート後のすべてのユーザーが実行可能。


    [PATH]

    - **id**: タスクID[reqired]

    [BODY]

    - **note**: ノート
    """
    checker = CkPermission(session=session, token=token)
    await checker.activate_only()

    service = AccountService()
    await service.put_watch_task(
        session=session, token=token, id=id, watch_task=watch_task
    )
    return {"detail": "Set watch-task successful."}


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


@router.delete(
    "/mine/watch-tasks/{id}/",
    name="mine:delete-watch-task",
    responses={
        401: {
            "model": Message,
            "description": "Auth Error",
            "content": {
                "application/json": {
                    "example": {"detail": "Authentication was unsuccessful."}
                }
            },
        },
        404: {
            "model": Message,
            "description": "Resource not found Error",
            "content": {
                "application/json": {"example": {"detail": "Resource not found."}}
            },
        },
        200: {
            "model": Message,
            "description": "Delete watch-task successful",
            "content": {
                "application/json": {
                    "example": {"detail": "Delete watch-task successful."}
                }
            },
        },
    },
)
async def delete_watch_task(
    id: int = p_task_id,
    session: AsyncSession = Depends(get_session),
    token: str = Depends(oauth2_scheme),
) -> Message:
    """
    監視タスクの解除。監視タスクとなっていない場合は何もしない。</br>
    アクティベート後のすべてのユーザーが実行可能。


    [PATH]

    - **id**: タスクID[reqired]
    """
    checker = CkPermission(session=session, token=token)
    await checker.activate_only()

    service = AccountService()
    await service.delete_watch_task(session=session, token=token, id=id)
    return {"detail": "Delete watch-task successful."}

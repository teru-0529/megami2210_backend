#!/usr/bin/python3
# accouts.py

from fastapi import APIRouter, Body, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.mine import oauth2_scheme
from app.api.schemas.accounts import (
    AccountCreate,
    PasswordReset,
    ProfileBaseUpdate,
    ProfileFilter,
    ProfilePublic,
    ProfilePublicList,
    ProfilePublicWithInitPass,
    p_account_id,
)
from app.api.schemas.base import Message, q_limit, q_offset, q_sort
from app.core.database import get_session
from app.services.accounts import AccountService
from app.services.permittion import CkPermission

router = APIRouter()

# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


@router.put(
    "/{id}/",
    name="accounts:create",
    responses={
        409: {
            "model": Message,
            "description": "Resource conflict Error",
            "content": {
                "application/json": {
                    "example": {"detail": "duplicate key: [account_id]."}
                }
            },
        },
        200: {
            "model": ProfilePublicWithInitPass,
            "description": "Create new account successful",
        },
    },
)
async def create(
    id: str = p_account_id,
    new_account: AccountCreate = Body(...),
    session: AsyncSession = Depends(get_session),
    token: str = Depends(oauth2_scheme),
) -> ProfilePublicWithInitPass:
    """
    アカウントの新規作成。</br>
    作成したアカウントは非Active状態。発行した初期パスワードを変更することでアクティベートされる。</br>
    ADMINユーザーのみ実行可能。

    [PATH]

    - **id**: アカウントID[reqired]

    [BODY]

    - **user_name**: ユーザー氏名[reqired]
    - **email**: Eメールアドレス[reqired]
    - **account_type**: アカウント種類[default=GENERAL]
    - **init_password**: 初期パスワード ※未設定の場合は内部でランダムに生成する
    """
    checker = CkPermission(session=session, token=token)
    await checker.activate_and_admin()

    service = AccountService()
    created_account = await service.create(
        session=session, id=id, new_account=new_account
    )
    return created_account


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


@router.get(
    "/{id}/profile",
    name="accounts:get-profile",
    responses={
        404: {
            "model": Message,
            "description": "Resource not found Error",
            "content": {
                "application/json": {"example": {"detail": "Resource not found."}}
            },
        },
        200: {"model": ProfilePublic, "description": "Get profile successful"},
    },
)
async def get_profile(
    id: str = p_account_id,
    session: AsyncSession = Depends(get_session),
    token: str = Depends(oauth2_scheme),
) -> ProfilePublic:
    """
    アカウント1件の取得。</br>
    PROVISIONALユーザーは実行不可。

    [PATH]

    - **id**: アカウントID[reqired]
    """
    checker = CkPermission(session=session, token=token)
    await checker.activate_and_upper_general()

    service = AccountService()
    account = await service.get_by_id(session=session, id=id)
    return account


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


@router.patch(
    "/{id}/profile",
    name="accounts:patch-profile",
    responses={
        409: {
            "model": Message,
            "description": "Resource conflict Error",
            "content": {
                "application/json": {
                    "example": {"detail": "duplicate key: [user_name]."}
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
        200: {"model": ProfilePublic, "description": "Update profile successful"},
    },
)
async def patch_profile(
    id: str = p_account_id,
    patch_params: ProfileBaseUpdate = Body(...),
    session: AsyncSession = Depends(get_session),
    token: str = Depends(oauth2_scheme),
) -> ProfilePublic:
    """
    管理者によるアカウント1件の更新。</br>
    ADMINユーザーのみ実行可能。</br>
    **nickname**、**email** は本人管轄項目のため変更できない。

    [PATH]

    - **id**: アカウントID[reqired]

    [BODY]

    - **user_name**: ユーザー氏名[not-nullable]
    - **account_type**: アカウント種別[not-nullable]
    """
    checker = CkPermission(session=session, token=token)
    await checker.activate_and_admin()

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
            "description": "Resource not found Error",
            "content": {
                "application/json": {"example": {"detail": "Resource not found."}}
            },
        },
        200: {"model": ProfilePublic, "description": "Delete account successful"},
    },
)
async def delete(
    id: str = p_account_id,
    session: AsyncSession = Depends(get_session),
    token: str = Depends(oauth2_scheme),
) -> ProfilePublic:
    """
    アカウント1件の削除。</br>
    ADMINユーザーのみ実行可能。

    [PATH]

    - **id**: アカウントID[reqired]

    """
    checker = CkPermission(session=session, token=token)
    await checker.activate_and_admin()

    service = AccountService()
    account = await service.delete(session=session, id=id)
    return account


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


@router.patch(
    "/{id}/password",
    name="accounts:password-reset",
    responses={
        404: {
            "model": Message,
            "description": "Resource not found Error",
            "content": {
                "application/json": {"example": {"detail": "Resource not found."}}
            },
        },
        200: {"model": PasswordReset, "description": "Reset password successful"},
    },
)
async def reset_password(
    id: str = p_account_id,
    pass_reset: PasswordReset = Body(...),
    session: AsyncSession = Depends(get_session),
    token: str = Depends(oauth2_scheme),
) -> PasswordReset:
    """
    パスワードのリセット。</br>
    アカウントを非Active化し初期パスワード再発行する。変更することでアカウントが再度アクティベートされる。</br>
    ADMINユーザーのみ実行可能。

    [PATH]

    - **id**: アカウントID[reqired]

    [BODY]

    - **init_password**: 初期パスワード ※未設定の場合は内部でランダムに生成する
    """
    checker = CkPermission(session=session, token=token)
    await checker.activate_and_admin()

    service = AccountService()
    init_pass = await service.password_reset(
        session=session, id=id, pass_reset=pass_reset
    )
    return init_pass


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


@router.post(
    "/search/profile",
    tags=["search"],
    name="accounts:search-profile",
    responses={
        200: {
            "model": ProfilePublicList,
            "description": "Search profiles successful",
        },
    },
)
async def search(
    offset: int = q_offset,
    limit: int = q_limit,
    sort: str = q_sort(default="+account_id", example="+account_type,-account_id"),
    filter: ProfileFilter = Body(...),
    session: AsyncSession = Depends(get_session),
    token: str = Depends(oauth2_scheme),
) -> ProfilePublicList:
    """
    プロフィール検索。</br>
    PROVISIONALユーザーは実行不可。</br>
    ※QUERYメソッドが提案されているが現状未実装のため、POSTメソッド、サブリソースを利用した対応

    [QUERY]

    - **offset**: 結果抽出時のオフセット値[default=0]
    - **limit**: 結果抽出時の最大件数[default=10] ※1システム制限として最大1000件まで指定可能
    - **sort**: ソートキー[default=+id] ※2[+deadline,-asaignee_id] のように複数指定可能。+:ASC、-:DESC
        - 指定可能キー: `account_id`, `user_name`, `nickname`, `email`, `verified_email`, `account_type`, `is_active`

    [BODY]

    - **account_id_sw**: <クエリ条件> アカウントID[START_WITH]
    - **user_name_cn**: <クエリ条件> 氏名[CONTAINS]
    - **nickname_cn**: <クエリ条件> ニックネーム[CONTAINS] ※1「nickname_cn」「nickname_ex」はいずれか一方のみ指定可能
    - **nickname_ex**: <クエリ条件> ニックネーム[EXIST] ※1
    - **email_dm**: <クエリ条件> メールアドレス[DOMAIN]
    - **verified_email_eq**: <クエリ条件> メール送達確認済み[EQUAL]
    - **account_type_in**: <クエリ条件> アカウント種別[IN]
    - **is_active_eq**: <クエリ条件> アクティベート済み[EQUAL]
    """
    checker = CkPermission(session=session, token=token)
    await checker.activate_and_upper_general()

    service = AccountService()
    profiles = await service.search(offset, limit, sort, session=session, filter=filter)
    return profiles

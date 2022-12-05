#!/usr/bin/python3
# accounts.py

from typing import List

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import (
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from app.api.schemas.accounts import (
    AccountCreate,
    PasswordChange,
    PasswordReset,
    ProfileBaseUpdate,
    ProfileInDB,
    ProfilePublic,
    ProfilePublicWithInitPass,
    ProfileUpdate,
    ProfileFilter,
    ProfilePublicList,
)
from app.api.schemas.token import AccessToken
from app.models.table_models import ac_Auth, ac_Profile
from app.repositries import QueryParam
from app.repositries.accounts import AccountRepository
from app.services import auth_service

# 未認証例外
not_authorized_exception: HTTPException = HTTPException(
    status_code=HTTP_401_UNAUTHORIZED,
    detail="No authenticated user.",
    headers={"WWW-Authenticate": "Bearer"},
)

# 対象無し例外
not_found_exception: HTTPException = HTTPException(
    status_code=HTTP_404_NOT_FOUND,
    detail="Account resource not found by specified Id.",
)

# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class AccountService:

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    async def create(
        self, *, session: AsyncSession, id: str, new_account: AccountCreate
    ) -> ProfilePublicWithInitPass:

        """アカウント登録"""
        profile = ac_Profile(**new_account.dict(exclude={"init_password"}))
        profile.account_id = id

        init_password = (
            new_account.init_password
            if new_account.init_password
            else auth_service.generate_init_password()
        )
        hashed_password, solt = auth_service.create_hash_password(init_password)

        auth = ac_Auth(
            account_id=id, email=new_account.email, password=hashed_password, solt=solt
        )

        repo = AccountRepository()
        try:
            created_profile = await repo.create(
                session=session, profile=profile, auth=auth
            )
            await session.commit()
        except IntegrityError as e:
            await session.rollback()
            self.ch_exception_detail(e)

        await session.refresh(created_profile)
        result = ProfileInDB.from_orm(created_profile)
        return ProfilePublicWithInitPass(init_password=init_password, **result.dict())

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    async def get_by_id(self, *, session: AsyncSession, id: str) -> ProfilePublic:

        """アカウント取得"""
        repo = AccountRepository()
        profile: ac_Profile = await repo.get_profile_by_id(session=session, id=id)
        if not profile:
            raise not_found_exception

        return ProfileInDB.from_orm(profile)

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    async def patch_base_profile(
        self, *, session: AsyncSession, id: str, patch_params: ProfileBaseUpdate
    ) -> ProfilePublic:

        """アカウント更新(base profile)"""
        update_dict = patch_params.dict(exclude_unset=True)
        return await self.update(session=session, id=id, update_dict=update_dict)

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----
    # [INNER]patch処理を共通化
    async def update(
        self, *, session: AsyncSession, id: str, update_dict: dict
    ) -> ProfilePublic:

        repo = AccountRepository()
        try:
            updated_profile: ac_Profile = await repo.update(
                session=session, id=id, patch_params=update_dict
            )
            await session.commit()
        except IntegrityError as e:
            await session.rollback()
            self.ch_exception_detail(e)
        if not updated_profile:
            raise not_found_exception

        await session.refresh(updated_profile)
        return ProfileInDB.from_orm(updated_profile)

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    async def delete(self, *, session: AsyncSession, id: str) -> ProfilePublic:

        """アカウント削除"""
        repo = AccountRepository()
        deleted_profile: ac_Profile = await repo.delete(session=session, id=id)
        if not deleted_profile:
            await session.rollback()
            raise not_found_exception

        await session.commit()
        return ProfileInDB.from_orm(deleted_profile)

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    async def login(
        self, *, session: AsyncSession, id: str, password: str
    ) -> AccessToken:

        """ログイン認証"""

        repo = AccountRepository()
        profile: ac_Profile = await repo.login_authentication(
            session=session, id=id, password=password
        )
        if not profile:
            raise not_authorized_exception
        token = auth_service.create_token_for_user(
            account=ProfileInDB.from_orm(profile)
        )
        return AccessToken(access_token=token, token_type="bearer")

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    async def get_my_profile(
        self, *, session: AsyncSession, token: str
    ) -> ProfilePublic:

        """ログインユーザーのプロフィール取得"""

        account_id = auth_service.get_id_from_token(token=token)
        profile = await self.get_by_id(session=session, id=account_id)

        return ProfileInDB.from_orm(profile)

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    async def patch_my_profile(
        self, *, session: AsyncSession, token: str, patch_params: ProfileUpdate
    ) -> ProfilePublic:

        """ログインユーザーのプロフィール更新"""

        account_id = auth_service.get_id_from_token(token=token)
        update_dict = patch_params.dict(exclude_unset=True)
        return await self.update(
            session=session, id=account_id, update_dict=update_dict
        )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    async def change_my_password(
        self, *, session: AsyncSession, token: str, pass_change: PasswordChange
    ) -> None:

        """ログインユーザーのパスワード変更"""

        account_id = auth_service.get_id_from_token(token=token)
        repo = AccountRepository()
        await repo.password_change(
            session=session,
            id=account_id,
            new_password=pass_change.new_password.get_secret_value(),
        )
        await session.commit()

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    async def password_reset(
        self, *, session: AsyncSession, id: str, pass_reset: PasswordReset
    ) -> PasswordReset:

        """パスワードリセット"""

        init_password = (
            pass_reset.init_password
            if pass_reset.init_password
            else auth_service.generate_init_password()
        )

        repo = AccountRepository()
        await repo.password_reset(session=session, id=id, password=init_password)
        await session.commit()

        return PasswordReset(init_password=init_password)

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    async def search(
        self,
        offset: int,
        limit: int,
        sort: str,
        *,
        session: AsyncSession,
        filter: ProfileFilter
    ) -> ProfilePublicList:
        """プロフィール照会"""

        query_param = self.New_QueryParam(
            offset=offset, limit=limit, sort=sort, filter=filter
        )
        repo = AccountRepository()
        searched_profiles: List[ac_Profile] = await repo.search(
            session=session, query_param=query_param
        )
        profiles: List[ProfilePublic] = [
            ProfileInDB.from_orm(profile) for profile in searched_profiles
        ]
        count: int = await repo.count(session=session, query_param=query_param)
        return ProfilePublicList(profiles=profiles, count=count)

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----
    # [INNER]クエリパラメータクラスの作成
    def New_QueryParam(
        self, *, offset: int, limit: int, sort: str, filter: ProfileFilter
    ) -> QueryParam:
        try:
            queryParm = QueryParam(
                columns=ac_Profile.__table__.columns,
                offset=offset,
                limit=limit,
                sort=sort,
                default_key="+account_id",
            )
        except ValueError as e:
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail=e.args
            )
        if filter.account_id_sw is not None:
            queryParm.append_filter(
                ac_Profile.account_id.startswith(filter.account_id_sw)
            )
        if filter.user_name_cn is not None:
            queryParm.append_filter(ac_Profile.user_name.contains(filter.user_name_cn))
        if filter.nickname_cn is not None:
            queryParm.append_filter(ac_Profile.nickname.contains(filter.nickname_cn))
        if filter.nickname_ex is True:
            queryParm.append_filter(ac_Profile.nickname.is_not(None))
        if filter.nickname_ex is False:
            queryParm.append_filter(ac_Profile.nickname.is_(None))
        if filter.email_dm is not None:
            queryParm.append_filter(ac_Profile.email.endswith("@" + filter.email_dm))
        if filter.verified_email_eq is not None:
            queryParm.append_filter(
                ac_Profile.verified_email.is_(filter.verified_email_eq)
            )
        if filter.account_type_in is not None:
            queryParm.append_filter(ac_Profile.account_type.in_(filter.account_type_in))
        if filter.is_active_eq is not None:
            queryParm.append_filter(ac_Profile.is_active.is_(filter.is_active_eq))
        return queryParm

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----
    # [INNER]例外文字列の判定
    def ch_exception_detail(self, e: IntegrityError) -> None:
        args = e.orig.args[0]
        if self.exists_params(
            args,
            [
                "asyncpg.exceptions.UniqueViolationError",
                "duplicate key",
                "account_id",
            ],
        ):
            raise HTTPException(
                status_code=HTTP_409_CONFLICT, detail="duplicate key: [account_id]."
            )
        elif self.exists_params(
            args,
            [
                "asyncpg.exceptions.UniqueViolationError",
                "duplicate key",
                "user_name",
            ],
        ):
            raise HTTPException(
                status_code=HTTP_409_CONFLICT, detail="duplicate key: [user_name]."
            )
        elif self.exists_params(
            args,
            [
                "asyncpg.exceptions.UniqueViolationError",
                "duplicate key",
                "email",
            ],
        ):
            raise HTTPException(
                status_code=HTTP_409_CONFLICT, detail="duplicate key: [email]."
            )
        raise e  # pragma: no cover

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----
    # [INNER]例外文字列の判定（指定文字列を含むか否か）
    def exists_params(self, args: str, params: List[str]) -> bool:
        filtered = [x for x in params if x in args]
        return filtered == params

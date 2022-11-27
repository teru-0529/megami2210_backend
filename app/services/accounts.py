#!/usr/bin/python3
# accounts.py

from typing import List

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
)

from app.api.schemas.accounts import (
    AccountCreate,
    InitPass,
    PasswordChange,
    PasswordReset,
    ProfileBaseUpdate,
    ProfileInDB,
    ProfilePublic,
    ProfileUpdate,
)
from app.api.schemas.token import AccessToken
from app.models.table_models import ac_Auth, ac_Profile
from app.repositries.accounts import AccountRepository
from app.services import auth_service
from app.services.authentication import AuthError

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
    ) -> ProfilePublic:

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
        result.init_password = init_password
        return result

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    async def get_by_id(self, *, session: AsyncSession, id: str) -> ProfilePublic:

        """アカウント取得"""
        repo = AccountRepository()
        profile: ac_Profile = await repo.get_profile_by_id(session=session, id=id)
        if not profile:
            raise not_found_exception

        return ProfileInDB.from_orm(profile)

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    async def patch_profile(
        self, *, session: AsyncSession, id: str, patch_params: ProfileUpdate
    ) -> ProfilePublic:

        """アカウント更新(profile)"""
        update_dict = patch_params.dict(exclude_unset=True)
        return await self.update(session=session, id=id, update_dict=update_dict)

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
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Authentication was unsuccessful.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token = auth_service.create_token_for_user(
            account=ProfileInDB.from_orm(profile)
        )
        return AccessToken(access_token=token, token_type="bearer")

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    async def get_mine(self, *, session: AsyncSession, token: str) -> ProfilePublic:

        """ログインユーザー情報の取得"""

        try:
            account_id = auth_service.get_id_from_token(token=token)
            profile = await self.get_by_id(session=session, id=account_id)
        except Exception:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="No authenticated user.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not profile:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="No authenticated user.",
                headers={"WWW-Authenticate": "Bearer"},
            )
            # if not current_account.is_active: #FIXME:
            #     raise HTTPException(
            #         status_code=HTTP_401_UNAUTHORIZED,
            #         detail="Not an active user.",
            #         headers={"WWW-Authenticate": "Bearer"},
            #     )

        print(profile)
        return ProfileInDB.from_orm(profile)

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    async def password_change(
        self, *, session: AsyncSession, id: str, pass_change: PasswordChange
    ) -> None:

        """パスワード変更"""

        repo = AccountRepository()
        try:
            await repo.password_change(
                session=session,
                id=id,
                old_password=pass_change.old_password.get_secret_value(),
                new_password=pass_change.new_password.get_secret_value(),
            )
            await session.commit()
        except AuthError:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Authentication was unsuccessful.",
            )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    async def password_reset(
        self, *, session: AsyncSession, id: str, pass_reset: PasswordReset
    ) -> InitPass:

        """パスワードリセット"""

        init_password = (
            pass_reset.init_password
            if pass_reset.init_password
            else auth_service.generate_init_password()
        )

        repo = AccountRepository()
        await repo.password_reset(session=session, id=id, password=init_password)
        await session.commit()

        return InitPass(init_password=init_password)

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
                status_code=HTTP_400_BAD_REQUEST, detail="duplicate key: [account_id]."
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
                status_code=HTTP_400_BAD_REQUEST, detail="duplicate key: [user_name]."
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
                status_code=HTTP_400_BAD_REQUEST, detail="duplicate key: [email]."
            )
        raise e  # pragma: no cover

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----
    # [INNER]例外文字列の判定（指定文字列を含むか否か）
    def exists_params(self, args: str, params: List[str]) -> bool:
        filtered = [x for x in params if x in args]
        return filtered == params

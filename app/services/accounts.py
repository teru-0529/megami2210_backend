#!/usr/bin/python3
# accounts.py

from typing import List

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from app.api.schemas.accounts import (
    AccountCreate,
    ProfileBaseUpdate,
    ProfileInDB,
    ProfilePublic,
    ProfileUpdate,
)
from app.models.table_models import ac_Auth, ac_Profile
from app.repositries.accounts import AccountRepository

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

        """アカウント登録"""  # FIXME: 初期パスワード
        profile = ac_Profile(**new_account.dict())
        profile.account_id = id

        auth = ac_Auth()
        auth.account_id = id
        auth.email = new_account.email
        auth.solt = "12345"  # FIXME:
        auth.password = "abcdef"  # FIXME:

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
        return ProfileInDB.from_orm(created_profile)

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    async def get_by_id(self, *, session: AsyncSession, id: str) -> ProfilePublic:

        """アカウント取得"""
        repo = AccountRepository()
        profile: ac_Profile = await repo.get_by_id(session=session, id=id)
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

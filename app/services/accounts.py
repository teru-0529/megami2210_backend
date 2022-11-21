#!/usr/bin/python3
# accounts.py

from typing import List

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from app.api.schemas.accounts import UserCreate, UserPublic
from app.models.table_models import ac_Auth, ac_Profile
from app.repositries.accounts import AccountRepository


class AccountService:
    async def create(
        self, *, session: AsyncSession, id: str, new_account: UserCreate
    ) -> UserPublic:
        """アカウント登録"""
        profile_d: dict = new_account.dict(exclude={"email", "account_type"})
        profile_d["account_id"] = id
        profile = ac_Profile(**profile_d)

        auth_d = new_account.dict(exclude={"user_name"}, exclude_unset=True)
        auth_d["account_id"] = id
        auth_d["solt"] = "12345"  # FIXME:
        auth_d["password"] = "abcdefg"  # FIXME:
        auth = ac_Auth(**auth_d)

        repo = AccountRepository()
        try:
            profile, auth = await repo.create(
                session=session, profile=profile, auth=auth
            )

            await session.commit()
        except IntegrityError as e:
            await session.rollback()
            self.ch_exception_detail(e)

        await session.refresh(profile)
        await session.refresh(auth)
        return self.NewUserPublic(profile=profile, auth=auth)
        result = UserPublic(
            account_id=profile.account_id,
            user_name=profile.user_name,
            email=auth.email,
            account_type=auth.account_type,
            is_active=auth.is_active,
            verified_email=auth.verified_email,
        )
        return result

    async def get_by_id(self, *, session: AsyncSession, id: str) -> UserPublic:
        """アカウント取得"""
        repo = AccountRepository()
        account: tuple[ac_Profile, ac_Auth] = await repo.get_by_id(
            session=session, id=id
        )

        self._ck_not_found(account)
        print(account)
        return self.NewUserPublic(profile=account[0], auth=account[1])

    def _ck_not_found(self, account: tuple[ac_Profile, ac_Auth]):
        if account is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Account resource not found by specified Id.",
            )

    def ch_exception_detail(self, e: IntegrityError) -> None:
        args = e.orig.args[0]
        if self.ch_exception_args(
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
        elif self.ch_exception_args(
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
        elif self.ch_exception_args(
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

    def ch_exception_args(self, args: str, params: List[str]) -> bool:
        filtered = [x for x in params if x in args]
        return filtered == params

    def NewUserPublic(self, profile: ac_Profile, auth: ac_Auth) -> UserPublic:
        return UserPublic(
            account_id=profile.account_id,
            user_name=profile.user_name,
            email=auth.email,
            account_type=auth.account_type,
            is_active=auth.is_active,
            verified_email=auth.verified_email,
        )

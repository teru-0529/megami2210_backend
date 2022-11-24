#!/usr/bin/python3
# accouts.py

from typing import Optional, Tuple

from sqlalchemy import select
from sqlalchemy.engine import Result
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.table_models import ac_Auth, ac_Profile
from app.services import auth_service
from app.services.authentication import AuthError

# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class AccountRepository:

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    async def create(
        self, *, session: AsyncSession, profile: ac_Profile, auth: ac_Auth
    ) -> Tuple[ac_Profile, ac_Auth]:

        """アカウント登録"""
        try:
            session.add(profile)
            session.add(auth)
            await session.flush()
        except IntegrityError as e:
            raise e
        return profile

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    async def update(
        self, *, session: AsyncSession, id: str, patch_params: dict[str, any]
    ) -> Optional[ac_Profile]:

        """アカウント更新"""
        base_profile: ac_Profile = await self.get_profile_by_id(
            session=session, id=id, for_update=True
        )
        if base_profile is None:
            return None

        # patch_paramsのフィールドを反映
        {
            setattr(base_profile, f, v)
            for f, v in patch_params.items()
            if f in base_profile.__dict__
        }

        await session.flush()
        return base_profile

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    async def delete(self, *, session: AsyncSession, id: str) -> Optional[ac_Profile]:

        """アカウント削除"""
        base_profile: ac_Profile = await self.get_profile_by_id(
            session=session, id=id, for_update=True
        )
        if base_profile is None:
            return None

        await session.delete(base_profile)
        await session.flush()
        return base_profile

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    async def get_profile_by_id(
        self, *, session: AsyncSession, id: str, for_update: bool = False
    ) -> Optional[ac_Profile]:

        """アカウント取得"""
        query = select(ac_Profile).filter(ac_Profile.account_id == id)
        if for_update:
            query = query.with_for_update()
        result: Result = await session.execute(query)
        profile: Optional[Tuple[ac_Profile]] = result.first()
        return profile[0] if profile else None

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    async def password_change(
        self, *, session: AsyncSession, id: str, old_password: str, new_password: str
    ) -> None:

        """パスワード変更"""
        base_auth: ac_Auth = await self._get_auth_by_id(session=session, id=id)
        if base_auth is None:
            return None
        # 現パスワードチェック
        if not auth_service.check_password(old_password, base_auth.password):
            raise AuthError
        # パスワードのhash化/反映
        hashed_password, solt = auth_service.create_hash_password(new_password)
        base_auth.password = hashed_password
        base_auth.solt = solt

        base_profile: ac_Profile = await self.get_profile_by_id(
            session=session, id=id, for_update=True
        )
        if base_profile is None:
            return None
        # アカウントのアクティブ化
        base_profile.is_active = True

        await session.flush()

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    async def password_reset(
        self, *, session: AsyncSession, id: str, password: str
    ) -> None:

        """パスワードリセット"""
        base_auth: ac_Auth = await self._get_auth_by_id(session=session, id=id)
        if base_auth is None:
            return None
        # パスワードのhash化/反映
        hashed_password, solt = auth_service.create_hash_password(password)
        base_auth.password = hashed_password
        base_auth.solt = solt

        base_profile: ac_Profile = await self.get_profile_by_id(
            session=session, id=id, for_update=True
        )
        if base_profile is None:
            return None
        # アカウントの非アクティブ化
        base_profile.is_active = False

        await session.flush()

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    async def _get_auth_by_id(
        self, *, session: AsyncSession, id: str
    ) -> Optional[ac_Auth]:

        """アカウント取得"""
        query = select(ac_Auth).filter(ac_Auth.account_id == id).with_for_update()
        result: Result = await session.execute(query)
        auth: Optional[Tuple[ac_Auth]] = result.first()
        return auth[0] if auth else None

#!/usr/bin/python3
# accouts.py

from typing import Optional, Tuple

from sqlalchemy import select
from sqlalchemy.engine import Result
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.table_models import ac_Auth, ac_Profile

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
        base_profile: ac_Profile = await self.get_by_id(
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
        base_profile: ac_Profile = await self.get_by_id(
            session=session, id=id, for_update=True
        )
        if base_profile is None:
            return None

        await session.delete(base_profile)
        await session.flush()
        return base_profile

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    async def get_by_id(
        self, *, session: AsyncSession, id: str, for_update: bool = False
    ) -> Optional[ac_Profile]:

        """アカウント取得"""
        query = select(ac_Profile).filter(ac_Profile.account_id == id)
        if for_update:
            query = query.with_for_update()
        result: Result = await session.execute(query)
        profile: Optional[Tuple[ac_Profile]] = result.first()
        return profile[0] if profile else None

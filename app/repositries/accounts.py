#!/usr/bin/python3
# accouts.py

from typing import Optional

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
    ) -> tuple[ac_Profile, ac_Auth]:

        """アカウント登録"""
        try:
            session.add(profile)
            session.add(auth)
            await session.flush()
        except IntegrityError as e:
            raise e
        return (profile, auth)

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    async def update(
        self, *, session: AsyncSession, id: str, patch_params: dict[str, any]
    ) -> Optional[tuple[ac_Profile, ac_Auth]]:

        """アカウント更新"""
        result: tuple[ac_Profile, ac_Auth] = await self.get_by_id(
            session=session, id=id, for_update=True
        )
        if result is None:
            return None

        profile, auth = result

        # patch_paramsのフィールドを反映
        {
            setattr(profile, f, v)
            for f, v in patch_params.items()
            if f in profile.__dict__
        }
        {setattr(auth, f, v) for f, v in patch_params.items() if f in auth.__dict__}

        await session.flush()
        return result

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    async def delete(
        self, *, session: AsyncSession, id: str
    ) -> Optional[tuple[ac_Profile, ac_Auth]]:

        """アカウント削除"""
        result: tuple[ac_Profile, ac_Auth] = await self.get_by_id(
            session=session, id=id, for_update=True
        )
        if result is None:
            return None

        await session.delete(result[0])
        await session.flush()
        return result

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    async def get_by_id(
        self, *, session: AsyncSession, id: str, for_update: bool = False
    ) -> Optional[tuple[ac_Profile, ac_Auth]]:

        """アカウント取得"""
        query = (
            select(ac_Profile, ac_Auth)
            .join(ac_Auth, ac_Profile.account_id == ac_Auth.account_id)
            .filter(ac_Profile.account_id == id)
        )
        if for_update:
            query = query.with_for_update()
        result: Result = await session.execute(query)
        return result.first()

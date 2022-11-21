#!/usr/bin/python3
# accouts.py

from typing import Optional

from sqlalchemy import select
from sqlalchemy.engine import Result

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.table_models import ac_Auth, ac_Profile


class AccountRepository:
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

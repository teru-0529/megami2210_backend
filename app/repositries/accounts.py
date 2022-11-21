#!/usr/bin/python3
# accouts.py

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

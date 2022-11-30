#!/usr/bin/python3
# permission.py

from sqlalchemy.ext.asyncio import AsyncSession
from app.services.accounts import AccountService
from app.api.schemas.accounts import ProfileInDB
from fastapi import HTTPException
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN
from app.models.segment_values import AccountTypes


# 非アクティベート例外
non_active_exception: HTTPException = HTTPException(
    status_code=HTTP_401_UNAUTHORIZED,
    detail="Not an active user.",
    headers={"WWW-Authenticate": "Bearer"},
)

# 権限なし例外
permission_exception: HTTPException = HTTPException(
    status_code=HTTP_403_FORBIDDEN,
    detail="Without permission user.",
)


class CkPermission:
    session: AsyncSession
    token: str

    def __init__(self, session: AsyncSession, token: str) -> None:
        self.session = session
        self.token = token

    async def activate_only(self) -> None:
        profile = await self._profile()
        if profile.is_active is False:
            raise non_active_exception

    async def activate_and_upper_general(self) -> None:
        profile = await self._profile()
        if profile.is_active is False:
            raise non_active_exception
        if profile.account_type not in (
            AccountTypes.administrator,
            AccountTypes.general,
        ):
            raise permission_exception

    async def activate_and_admin(self) -> None:
        profile = await self._profile()
        if profile.is_active is False:
            raise non_active_exception
        if not profile.account_type == AccountTypes.administrator:
            raise permission_exception

    async def _profile(self) -> ProfileInDB:
        account_service = AccountService()
        profile = await account_service.get_my_profile(
            session=self.session, token=self.token
        )
        return profile

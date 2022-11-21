#!/usr/bin/python3
# accounts.py

from typing import Optional

from pydantic import Extra, Field, EmailStr
from fastapi import Path

from app.api.schemas.base import CoreModel
from app.models.segment_values import AccountTypes

p_account_id: str = Path(
    title="AccountId",
    description="アカウントID",
    min_length=5,
    max_length=5,
    example="T-001",
)

f_account_id: Field = Field(
    title="AccountId",
    description="アカウントID",
    min_length=5,
    max_length=5,
    example="T-001",
)
f_user_name: Field = Field(
    title="UserName", description="ユーザー氏名", max_length=20, example="織田信長"
)
f_nickname: Field = Field(
    title="Nickname", description="ニックネーム", max_length=20, example="第六天魔王"
)
f_email: Field = Field(
    title="Email", description="Eメールアドレス", example="nobunaga@sengoku.com"
)
f_password: Field = Field(
    title="Password", description="サインインパスワード", min_length=8, example="password"
)
f_account_type: Field = Field(
    title="AccountType",
    description=AccountTypes.description(),
    example=AccountTypes.general,
)
f_is_active: Field = Field(
    title="IsActive", description="アクティベーション済みの場合にTrue", example=True
)
f_verified_email: Field = Field(
    title="VerifiedEmail", description="メール疎通確認済みの場合にTrue", example=True
)


class UserBase(CoreModel):
    account_id: str = f_account_id
    user_name: str = f_user_name
    nickname: Optional[str] = f_nickname
    email: EmailStr = f_email
    account_type: AccountTypes = f_account_type
    is_active: bool = f_is_active
    verified_email: bool = f_verified_email


class UserCreate(CoreModel, extra=Extra.forbid):
    user_name: str = f_user_name
    email: EmailStr = f_email
    account_type: Optional[AccountTypes] = f_account_type


class UserAuthorize(CoreModel, extra=Extra.forbid):
    account_id: str = f_account_id
    password: str = f_password


class UserUpdate(CoreModel, extra=Extra.forbid):
    nickname: Optional[str] = f_nickname
    email: Optional[EmailStr] = f_email


class UserUpdateByAdmin(CoreModel, extra=Extra.forbid):
    user_name: Optional[str] = f_user_name
    account_type: Optional[AccountTypes] = f_account_type


class UserInDB(UserBase):
    class Config:
        orm_mode = True


class UserPublic(UserBase):
    pass

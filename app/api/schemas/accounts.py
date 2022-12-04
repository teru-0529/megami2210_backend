#!/usr/bin/python3
# accounts.py

from typing import Optional

from fastapi import Path
from pydantic import EmailStr, Extra, Field, SecretStr, validator

from app.api.schemas.base import CoreModel
from app.models.segment_values import AccountTypes

# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+

# パスパラメータ
p_account_id: Path = Path(
    title="AccountId",
    description="アカウントID",
    min_length=5,
    max_length=5,
    example="T-901",
)

b_user_name: Field = Field(
    title="UserName", description="ユーザー氏名", max_length=20, example="織田信長"
)
b_nickname: Field = Field(
    title="Nickname", description="ニックネーム", max_length=20, example="第六天魔王"
)
b_email: Field = Field(
    title="Email", description="Eメールアドレス", example="nobunaga@sengoku.com"
)
b_password: Field = Field(
    title="Password", description="サインインパスワード", min_length=8, example="password"
)
b_account_type: Field = Field(
    default=AccountTypes.general,
    title="AccountType",
    description=AccountTypes.description(),
    example=AccountTypes.general,
)
b_is_active: Field = Field(
    title="IsActive", description="アクティベーション済みの場合にTrue", example=True
)
b_verified_email: Field = Field(
    title="VerifiedEmail", description="メール疎通確認済みの場合にTrue", example=True
)


def b_account_id(description: str = "アカウントID") -> Field:
    return Field(
        title="AccountId",
        description=description,
        min_length=5,
        max_length=5,
        example="T-901",
    )


def b_password(description: str = "サインインパスワード") -> Field:
    return Field(
        title="Password", description=description, min_length=8, example="password"
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class ProfileBase(CoreModel):
    account_id: str = b_account_id()
    user_name: str = b_user_name
    nickname: Optional[str] = b_nickname
    email: EmailStr = b_email
    account_type: AccountTypes = b_account_type
    is_active: bool = b_is_active
    verified_email: bool = b_verified_email
    # init_password: Optional[SecretStr] = b_password()


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class AccountCreate(CoreModel, extra=Extra.forbid):
    user_name: str = b_user_name
    email: EmailStr = b_email
    account_type: Optional[AccountTypes] = b_account_type
    init_password: Optional[str] = b_password("初期パスワード")


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class ProfileUpdate(CoreModel, extra=Extra.forbid):
    nickname: Optional[str] = b_nickname
    email: Optional[EmailStr] = b_email

    @validator("email")
    def not_none(cls, v):
        if v is None:
            raise ValueError("value is none.")
        return v


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class ProfileBaseUpdate(CoreModel, extra=Extra.forbid):
    user_name: Optional[str] = b_user_name
    account_type: Optional[AccountTypes] = b_account_type

    @validator("user_name", "account_type")
    def not_none(cls, v):
        if v is None:
            raise ValueError("value is none.")
        return v


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class ProfileInDB(ProfileBase):
    class Config:
        orm_mode = True


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class ProfilePublic(ProfileBase):
    pass


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class ProfilePublicWithInitPass(ProfilePublic):
    init_password: Optional[str] = b_password("初期パスワード")


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class PasswordChange(CoreModel, extra=Extra.forbid):
    new_password: SecretStr = b_password("新パスワード")


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class PasswordReset(CoreModel, extra=Extra.forbid):
    init_password: Optional[str] = b_password("初期パスワード")

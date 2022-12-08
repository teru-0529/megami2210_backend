#!/usr/bin/python3
# accounts.py

from typing import List, Optional

from fastapi import Path
from pydantic import EmailStr, Extra, Field, SecretStr, validator

from app.api.schemas.base import CoreModel, QueryModel
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


# ボディパラメータ(クエリメソッド用)
s_account_id_sw: Field = Field(
    title="AccountId-[START_WITH]",
    description="<クエリ条件> アカウントID(指定文字列で始まる)",
    max_length=5,
    example="T-9",
)
s_user_name_cn: Field = Field(
    title="UserName-[CONTAINS]",
    description="<クエリ条件> 氏名(指定文字列を含む)",
    max_length=20,
    example="徳川",
)
s_nickname_cn: Field = Field(
    title="Nickname-[CONTAINS]",
    description="<クエリ条件> ニックネーム(指定文字列を含む)",
    max_length=20,
    example="魔王",
)
s_nickname_ex: Field = Field(
    title="Nickname-[EXIST]",
    description="<クエリ条件> ニックネーム(設定有無)",
    example=True,
)
s_email_dm: Field = Field(
    title="Email-[DOMAIN]",
    description="<クエリ条件> メールアドレス(ドメイン一致)",
    example="semgoku.com",
)
s_verified_email_eq: Field = Field(
    title="VerifiedEmail-[EQUAL]", description="<クエリ条件> メール送達確認済み(一致)", example=True
)
s_account_type_in: Field = Field(
    title="AccountType-[IN]",
    description="<クエリ条件> アカウント種別(リスト内のいずれかと一致)",
    example=[AccountTypes.administrator, AccountTypes.general],
    min_items=1,
)
s_is_active_eq: Field = Field(
    title="IsActive-[EQUAL]", description="<クエリ条件> アクティベート済み(一致)", example=True
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


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class ProfilePublicList(QueryModel):
    profiles: List[ProfileInDB] = Field(description="プロフィールリスト")


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class ProfileFilter(CoreModel, extra=Extra.forbid):
    account_id_sw: Optional[str] = s_account_id_sw
    user_name_cn: Optional[str] = s_user_name_cn
    nickname_cn: Optional[str] = s_nickname_cn
    nickname_ex: Optional[bool] = s_nickname_ex
    email_dm: Optional[str] = s_email_dm
    verified_email_eq: Optional[bool] = s_verified_email_eq
    account_type_in: Optional[List[AccountTypes]] = s_account_type_in
    is_active_eq: Optional[bool] = s_is_active_eq

    @validator("nickname_ex")
    def asaignee_id_ex_duplicate(cls, v, values):
        if "nickname_cn" in values and values["nickname_cn"] is not None:
            raise ValueError("keyword[nickname] is duplicate.")
        return v

    @validator("nickname_cn")
    def asaignee_id_cn_duplicate(cls, v, values):
        if "nickname_ex" in values and values["nickname_ex"] is not None:
            raise ValueError("keyword[nickname] is duplicate.")
        return v

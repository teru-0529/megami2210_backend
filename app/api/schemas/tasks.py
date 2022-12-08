#!/usr/bin/python3
# tasks.py

from datetime import date, datetime
from typing import List, Optional, Union

from fastapi import Path, Query
from pydantic import Extra, Field, validator

from app.api.schemas.accounts import ProfilePublic, b_account_id
from app.api.schemas.base import CoreModel, QueryModel
from app.models.segment_values import TaskStatus

# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+

# パスパラメータ
p_task_id: Path = Path(title="TaskId", description="タスクID", ge=1, example=10)

# クエリパラメータ
q_sub_resources: Query = Query(
    default=None,
    title="Include sub resources",
    description="レスポンスに含めるサブリソース",
    example="account",
    alias="sub-resources",
)

# ボディパラメータ
b_task_id: Field = Field(title="TaskId", description="タスクID", ge=1, example=10)
b_title: Field = Field(
    title="TaskTitle", description="タスクの名称", example="create db model", max_length=30
)
b_description: Field = Field(
    title="Description", description="タスクの詳細内容", example="データベースモデルを作成する。"
)
b_status: Field = Field(
    title="TaskStatus", description=TaskStatus.description(), example=TaskStatus.todo
)
b_is_significant: Field = Field(
    default=False, title="IsSignificant", description="重要タスクの場合にTrue", example=True
)
b_deadline: Field = Field(
    title="Deadline",
    description="タスク期限日(YYYY-MM-DD) ※当日以降の日付を指定可能",
    example="2025-12-31",
)
b_note: Field = Field(title="Note", description="ノート", example="要チェック！")

# ボディパラメータ(クエリメソッド用)
s_title_cn: Field = Field(
    title="Title-[CONTAINS]",
    description="<クエリ条件> タスクの名称(指定文字列を含む)",
    example="タスク",
    max_length=30,
)
s_description_cn: Field = Field(
    title="Description-[CONTAINS]", description="<クエリ条件> タスク詳細(指定文字列を含む)", example="作成"
)
s_asagnee_id_in: Field = Field(
    title="AsagneeId-[IN]",
    description="<クエリ条件> タスク担当者(リスト内のいずれかと一致)",
    example=["T-901", "T-902"],
    min_items=1,
    max_items=3,
    min_length=5,
    max_length=5,
)
s_asagnee_id_ex: Field = Field(
    title="AsagneeId-[EXIST]",
    description="<クエリ条件> タスク担当者(設定有無)",
    example=True,
)
s_status_in: Field = Field(
    title="Status-[IN]",
    description="<クエリ条件> タスクステータス(リスト内のいずれかと一致)",
    example=[TaskStatus.todo, TaskStatus.doing],
    min_items=1,
)
s_is_significant_eq: Field = Field(
    title="IsSignificant-[EQUAL]", description="<クエリ条件> 重要フラグ(一致)", example=True
)
s_deadline_from: Field = Field(
    title="Deadline-[FROM]", description="<クエリ条件> タスク期限(FROM)", example="2022-11-01"
)
s_deadline_to: Field = Field(
    title="Deadline-[TO]", description="<クエリ条件> タスク期限(TO)", example="2022-11-30"
)

# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class TaskBase(CoreModel):
    id: int = b_task_id
    registrant_id: Optional[str] = b_account_id("登録者ID")
    title: str = b_title
    description: Optional[str] = b_description
    asaignee_id: Optional[str] = b_account_id("担当者ID")
    status: TaskStatus = b_status
    is_significant: bool = b_is_significant
    deadline: Optional[date] = b_deadline


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class TaskCreate(CoreModel, extra=Extra.forbid):
    title: str = b_title
    description: Optional[str] = b_description
    asaignee_id: Optional[str] = b_account_id("担当者ID")
    is_significant: bool = b_is_significant
    deadline: Optional[date] = b_deadline

    @validator("deadline")
    def is_after_today(cls, val: date):
        """値が設定されている場合は、今日以降の日付であること"""
        if val and val < datetime.today().date():
            raise ValueError("deadline must after today.")
        return val


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class TaskUpdate(CoreModel, extra=Extra.forbid):
    description: Optional[str] = b_description
    asaignee_id: Optional[str] = b_account_id("担当者ID")
    status: Optional[TaskStatus] = b_status
    deadline: Optional[date] = b_deadline

    @validator("deadline")
    def is_after_today(cls, val: date):
        """値が設定されている場合は、今日以降の日付であること"""
        if val and val < datetime.today().date():
            raise ValueError("deadline must after today.")
        return val


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class TaskInDB(TaskBase):
    class Config:
        orm_mode = True


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class TaskPublic(TaskBase):
    pass


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class TaskWithAccount(CoreModel):
    id: int = b_task_id
    registrant: Optional[ProfilePublic] = Field(
        title="ProfilePublic", description="登録者"
    )
    title: str = b_title
    description: Optional[str] = b_description
    asaignee: Optional[ProfilePublic] = Field(title="ProfilePublic", description="担当者")
    status: TaskStatus = b_status
    is_significant: bool = b_is_significant
    deadline: Optional[date] = b_deadline

    class Config:
        orm_mode = True


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class TaskPublicList(QueryModel):
    tasks: List[Union[TaskInDB, TaskWithAccount]] = Field(description="タスクリスト")


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class TaskFilter(CoreModel, extra=Extra.forbid):
    title_cn: Optional[str] = s_title_cn
    description_cn: Optional[str] = s_description_cn
    asaignee_id_in: Optional[List[str]] = s_asagnee_id_in
    asaignee_id_ex: Optional[bool] = s_asagnee_id_ex
    status_in: Optional[List[TaskStatus]] = s_status_in
    is_significant_eq: Optional[bool] = s_is_significant_eq
    deadline_from: Optional[date] = s_deadline_from
    deadline_to: Optional[date] = s_deadline_to

    @validator("asaignee_id_in")
    def asaignee_id_in_duplicate(cls, v, values):
        if "asaignee_id_ex" in values and values["asaignee_id_ex"] is not None:
            raise ValueError("keyword[asaignee_id] is duplicate.")
        return v

    @validator("asaignee_id_ex")
    def asaignee_id_ex_duplicate(cls, v, values):
        if "asaignee_id_in" in values and values["asaignee_id_in"] is not None:
            raise ValueError("keyword[asaignee_id] is duplicate.")
        return v

    @validator("deadline_to")
    def deadline_sequence(cls, to, values):
        if (
            to is not None
            and values["deadline_from"] is not None
            and values["deadline_from"] > to
        ):
            raise ValueError("[deadline_from] must faster than [deadline_to].")
        return to


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class WatchTask(CoreModel):
    note: Optional[str] = b_note


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class TaskWithWatchNote(TaskBase):
    note: str = b_note

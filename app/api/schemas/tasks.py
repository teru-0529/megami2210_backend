#!/usr/bin/python3
# tasks.py

from datetime import date, datetime
from typing import List, Optional

from fastapi import Path, Query
from pydantic import Field, validator

from app.api.schemas.base import CoreModel, IDModelMixin, QueryModel
from app.services.segment_values import TaskStatus

p_id: int = Path(title="ID", description="タスクID", ge=1, example=10)

q_exclude_asaignee: bool = Query(
    default=False,
    title="ExcludeAsaignee",
    description="担当者情報の詳細情報をレスポンスから除外する場合にTrue",
    example=True,
)


f_title: Field = Field(
    title="TaskTitle", max_length=30, description="タスクの名称", example="create db model"
)
f_description: Field = Field(
    title="Description", description="タスクの詳細内容", example="データベースモデルを作成する。"
)
f_asagnee_id: Field = Field(
    title="AsaigneeId", description="タスクの担当者", min_length=3, max_length=3, example="000"
)
f_status: Field = Field(
    title="TaskStatus", description=TaskStatus.description(), example="DOING"
)
f_is_significant: Field = Field(
    default=False, title="IsSignificant", description="重要タスクの場合にTrue", example=True
)
f_deadline: Field = Field(
    title="Deadline",
    description="タスク期限日(YYYY-MM-DD) ※当日以降の日付を指定可能",
    example="2022-12-31",
)


class TaskBase(CoreModel):
    title: str = f_title
    description: Optional[str] = f_description
    asaignee_id: Optional[str] = f_asagnee_id
    status: TaskStatus = f_status
    is_significant: bool = f_is_significant
    deadline: Optional[date] = f_deadline


class TaskCreate(CoreModel):
    title: str = f_title
    description: Optional[str] = f_description
    asaignee_id: Optional[str] = f_asagnee_id
    is_significant: bool = f_is_significant
    deadline: Optional[date] = f_deadline

    @validator("deadline")
    def is_after_today(cls, val: date):
        """値が設定されている場合は、今日以降の日付であること"""
        if val and val < datetime.today().date():
            raise ValueError("deadline must after today.")
        return val


class TaskUpdate(TaskBase):
    desctiption: str = f_description
    asaignee_id: str = f_asagnee_id
    status: TaskStatus = f_status


class TaskInDB(IDModelMixin, TaskBase):
    title: str = f_title
    status: TaskStatus = f_status
    is_significant: bool = f_is_significant

    class Config:
        orm_mode = True


class TaskPublic(IDModelMixin, TaskBase):
    pass


class TasksQuery(QueryModel):
    tasks: List[TaskPublic]

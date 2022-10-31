#!/usr/bin/python3
# tasks.py

from datetime import date, datetime
from enum import Enum
from typing import Optional

from app.api.schemas.base import CoreModel, IDModelMixin
from pydantic import Field, validator


class TaskStatus(str, Enum):
    todo = "TODO"
    doing = "DOING"
    done = "DONE"


task_status_description: str = """
タスク状況:
  * `TODO` - 未対応
  * `DOING` - 対応中
  * `DONE` - 完了
"""

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
    title="TaskStatus", description=task_status_description, example="DOING"
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
        """今日以降の日付であるチェック"""
        if val < datetime.today().date():
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

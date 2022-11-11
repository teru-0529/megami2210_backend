#!/usr/bin/python3
# tasks.py

from datetime import date, datetime
from typing import List, Optional

from fastapi import Path, Query
from pydantic import Field, validator

from app.api.schemas.base import CoreModel, IDModelMixin, QueryModel
from app.db.models import Task as task_model
from app.services.segment_values import TaskStatus

p_id: int = Path(title="ID", description="タスクID", ge=1, example=10)

q_exclude_asaignee: bool = Query(
    default=False,
    title="ExcludeAsaignee",
    description="担当者情報の詳細情報をレスポンスから除外する場合にTrue",
    example=True,
)


f_title: Field = Field(
    title="TaskTitle", description="タスクの名称", example="create db model", max_length=30
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

q_title_cn: Field = Field(
    title="Title-[CONTAINS]",
    description="<クエリ条件> タスクの名称(含む)",
    example="タスク",
    max_length=30,
)
q_description_cn: Field = Field(
    title="Description-[CONTAINS]", description="<クエリ条件> タスク詳細(含む)", example="作成"
)
q_asagnee_id_in: Field = Field(
    title="AsagneeId-[IN]",
    description="<クエリ条件> タスク担当者(いずれか)",
    example=["100", "200"],
    min_items=1,
    max_items=3,
    min_length=3,
    max_length=3,
)
q_asagnee_id_ex: Field = Field(
    title="AsagneeId-[EXIST]",
    description="<クエリ条件> タスク担当者(設定有無)",
    example=True,
)
q_status_in: Field = Field(
    title="Status-[IN]",
    description="<クエリ条件> タスクステータス(いずれか)",
    example=["TODO", "DOING"],
    min_items=1,
)
q_is_significant_eq: Field = Field(
    title="IsSignificant-[EQUAL]", description="<クエリ条件> 重要フラグ(一致)", example=True
)
q_deadline_from: Field = Field(
    title="Deadline-[FROM]", description="<クエリ条件> タスク期限(FROM)", example="2022-11-01"
)
q_deadline_to: Field = Field(
    title="Deadline-[TO]", description="<クエリ条件> タスク期限(TO)", example="2022-11-30"
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


class TasksQParam(CoreModel):
    title_cn: Optional[str] = q_title_cn
    descriotion_cn: Optional[str] = q_description_cn
    asaignee_id_in: Optional[List[str]] = q_asagnee_id_in
    asaignee_id_ex: Optional[bool] = q_asagnee_id_ex
    status_in: Optional[List[TaskStatus]] = q_status_in
    is_significant_eq: Optional[bool] = q_is_significant_eq
    deadline_from: Optional[date] = q_deadline_from
    deadline_to: Optional[date] = q_deadline_to

    @validator("asaignee_id_ex")
    def asaignee_id_duplicate(cls, v, values):
        if v is not None and values["asaignee_id_in"] is not None:
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

    def sql(self) -> List:
        ls = []
        if self.title_cn is not None:
            ls.append(task_model.title.contains(self.title_cn))
        if self.descriotion_cn is not None:
            ls.append(task_model.description.contains(self.descriotion_cn))
        if self.asaignee_id_in is not None:
            ls.append(task_model.asaignee_id.in_(self.asaignee_id_in))
        if self.asaignee_id_ex is True:
            ls.append(task_model.asaignee_id.is_not(None))
        if self.asaignee_id_ex is False:
            ls.append(task_model.asaignee_id.is_(None))
        if self.status_in is not None:
            ls.append(task_model.status.in_(self.status_in))
        if self.is_significant_eq is not None:
            ls.append(task_model.is_significant.is_(self.is_significant_eq))
        if self.deadline_from is not None:
            ls.append(task_model.deadline >= self.deadline_from)
        if self.deadline_to is not None:
            ls.append(task_model.deadline <= self.deadline_to)
        return ls

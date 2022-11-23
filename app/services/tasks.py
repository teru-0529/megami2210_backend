#!/usr/bin/python3
# tasks.py

from typing import List

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_404_NOT_FOUND, HTTP_422_UNPROCESSABLE_ENTITY

from app.api.schemas.tasks import (
    TaskCreate,
    TaskFilter,
    TaskInDB,
    TaskPublic,
    TaskPublicList,
    TaskUpdate,
)
from app.models.table_models import td_Task
from app.repositries import QueryParam
from app.repositries.tasks import TaskRepository

# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class TaskService:

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    async def create(
        self, *, session: AsyncSession, new_task: TaskCreate
    ) -> TaskPublic:
        """タスク登録"""
        task = td_Task(**new_task.dict())
        repo = TaskRepository()
        created_task: td_Task = await repo.create(session=session, task=task)

        await session.commit()
        await session.refresh(created_task)
        return TaskInDB.from_orm(created_task)

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    async def query(
        self,
        offset: int,
        limit: int,
        sort: str,
        execute_assaignee: bool,  # TODO:
        *,
        session: AsyncSession,
        filter: TaskFilter
    ) -> TaskPublicList:
        """タスク照会"""
        query_param = self.New_QueryParam(
            offset=offset, limit=limit, sort=sort, filter=filter
        )
        repo = TaskRepository()
        query_tasks: List[td_Task] = await repo.query(
            session=session, query_param=query_param
        )
        tasks: List[TaskPublic] = [TaskInDB.from_orm(task) for task in query_tasks]
        count: int = await repo.count(session=session, query_param=query_param)
        return TaskPublicList(tasks=tasks, count=count)

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    async def get_by_id(self, *, session: AsyncSession, id: int) -> TaskPublic:
        """タスク取得"""
        repo = TaskRepository()
        task: td_Task = await repo.get_by_id(session=session, id=id)

        self._ck_not_found(task)
        return TaskInDB.from_orm(task)

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    async def patch(
        self, *, session: AsyncSession, id: int, patch_params: TaskUpdate
    ) -> TaskPublic:
        """タスク更新"""
        update_dict = patch_params.dict(exclude_unset=True)
        repo = TaskRepository()
        updated_task: td_Task = await repo.update(
            session=session, id=id, patch_params=update_dict
        )
        self._ck_not_found(updated_task)

        await session.commit()
        await session.refresh(updated_task)
        return TaskInDB.from_orm(updated_task)

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    async def delete(self, *, session: AsyncSession, id: int) -> TaskPublic:
        """タスク削除"""
        repo = TaskRepository()
        deleted_task: td_Task = await repo.delete(session=session, id=id)
        self._ck_not_found(deleted_task)

        await session.commit()
        return TaskInDB.from_orm(deleted_task)

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----
    # [INNER]noneチェック
    def _ck_not_found(self, task: td_Task):
        if task is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Task resource not found by specified Id.",
            )

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----
    # [INNER]クエリパラメータクラスの作成
    def New_QueryParam(
        self, *, offset: int, limit: int, sort: str, filter: TaskFilter
    ) -> QueryParam:
        try:
            queryParm = QueryParam(
                columns=td_Task.__table__.columns, offset=offset, limit=limit, sort=sort
            )
        except ValueError as e:
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail=e.args
            )
        if filter.title_cn is not None:
            queryParm.append_filter(td_Task.title.contains(filter.title_cn))
        if filter.description_cn is not None:
            queryParm.append_filter(td_Task.description.contains(filter.description_cn))
        if filter.asaignee_id_in is not None:
            queryParm.append_filter(td_Task.asaignee_id.in_(filter.asaignee_id_in))
        if filter.asaignee_id_ex is True:
            queryParm.append_filter(td_Task.asaignee_id.is_not(None))
        if filter.asaignee_id_ex is False:
            queryParm.append_filter(td_Task.asaignee_id.is_(None))
        if filter.status_in is not None:
            queryParm.append_filter(td_Task.status.in_(filter.status_in))
        if filter.is_significant_eq is not None:
            queryParm.append_filter(
                td_Task.is_significant.is_(filter.is_significant_eq)
            )
        if filter.deadline_from is not None:
            queryParm.append_filter(td_Task.deadline >= filter.deadline_from)
        if filter.deadline_to is not None:
            queryParm.append_filter(td_Task.deadline <= filter.deadline_to)
        return queryParm

#!/usr/bin/python3
# tasks.py

from typing import List

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_404_NOT_FOUND, HTTP_422_UNPROCESSABLE_ENTITY

from app.api.schemas.tasks import (
    TaskCreate,
    TaskInDB,
    TaskPublic,
    TasksQParam,
    TasksQuery,
    TaskUpdate,
)
from app.db.query_conf import QueryConf
from app.db.repositries.tasks import TaskRepository
from app.models import m_Task


class TaskService:
    async def create(
        self, *, session: AsyncSession, new_task: TaskCreate
    ) -> TaskPublic:
        """タスク登録"""
        task = m_Task(**new_task.dict())
        task_repo = TaskRepository()
        created_task: m_Task = await task_repo.create(session=session, task=task)

        await session.commit()
        await session.refresh(created_task)
        return TaskInDB.from_orm(created_task)

    async def query(
        self,
        offset: int,
        limit: int,
        sort: str,
        execute_assaignee: bool,  # TODO:
        *,
        session: AsyncSession,
        qp: TasksQParam
    ) -> TasksQuery:
        """タスク照会"""
        try:
            qc = QueryConf(m_Task.__table__.columns, offset, limit, sort)
        except ValueError as e:
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail=e.args
            )

        task_repo = TaskRepository()
        query_tasks: List[m_Task] = await task_repo.query(session=session, qp=qp, qc=qc)
        tasks: List[TaskPublic] = [TaskInDB.from_orm(task) for task in query_tasks]
        count: int = await task_repo.count(session=session, qp=qp)
        return TasksQuery(tasks=tasks, count=count)

    async def get_by_id(self, *, session: AsyncSession, id: int) -> TaskPublic:
        """タスク取得"""
        task_repo = TaskRepository()
        get_task: m_Task = await task_repo.get_by_id(session=session, id=id)

        self._ck_not_found(get_task)
        return TaskInDB.from_orm(get_task)

    async def patch(
        self, *, session: AsyncSession, id: int, patch_params: TaskUpdate
    ) -> TaskPublic:
        """タスク更新"""
        update_dict = patch_params.dict(exclude_unset=True)
        task_repo = TaskRepository()
        updated_task: m_Task = await task_repo.update(
            session=session, id=id, patch_params=update_dict
        )
        self._ck_not_found(updated_task)

        await session.commit()
        await session.refresh(updated_task)
        return TaskInDB.from_orm(updated_task)

    async def delete(self, *, session: AsyncSession, id: int) -> TaskPublic:
        """タスク削除"""
        task_repo = TaskRepository()
        deleted_task: m_Task = await task_repo.delete(session=session, id=id)
        self._ck_not_found(deleted_task)

        await session.commit()
        return TaskInDB.from_orm(deleted_task)

    def _ck_not_found(self, task: m_Task):
        if task is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND, detail="指定されたidのタスクは見つかりませんでした。"
            )

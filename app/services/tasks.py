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
from app.db.models import Task as task_model
from app.db.query_conf import QueryConf
from app.db.repositries.tasks import TaskRepository


class TaskService:
    async def create(self, *, db: AsyncSession, new_task: TaskCreate) -> TaskPublic:
        """タスク登録"""
        task = task_model(**new_task.dict())
        task_repo = TaskRepository()
        created_task: task_model = await task_repo.create(db=db, task=task)

        await db.commit()
        await db.refresh(created_task)
        return TaskInDB.from_orm(created_task)

    async def query(
        self,
        offset: int,
        limit: int,
        sort: str,
        execute_assaignee: bool,  # TODO:
        *,
        db: AsyncSession,
        qp: TasksQParam
    ) -> TasksQuery:
        """タスク照会"""
        try:
            qc = QueryConf(task_model.__table__.columns, offset, limit, sort)
        except ValueError as e:
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail=e.args
            )

        task_repo = TaskRepository()
        query_tasks: List[task_model] = await task_repo.query(db=db, qp=qp, qc=qc)
        tasks: List[TaskPublic] = [TaskInDB.from_orm(task) for task in query_tasks]
        count: int = await task_repo.count(db=db, qp=qp)
        return TasksQuery(tasks=tasks, count=count)

    async def get_by_id(self, *, db: AsyncSession, id: int) -> TaskPublic:
        """タスク取得"""
        task_repo = TaskRepository()
        get_task: task_model = await task_repo.get_by_id(db=db, id=id)

        self._ck_not_found(get_task)
        return TaskInDB.from_orm(get_task)

    async def patch(
        self, *, db: AsyncSession, id: int, patch_params: TaskUpdate
    ) -> TaskPublic:
        """タスク更新"""
        update_dict = patch_params.dict(exclude_unset=True)
        task_repo = TaskRepository()
        updated_task: task_model = await task_repo.update(
            db=db, id=id, patch_params=update_dict
        )
        self._ck_not_found(updated_task)

        await db.commit()
        await db.refresh(updated_task)
        return TaskInDB.from_orm(updated_task)

    async def delete(self, *, db: AsyncSession, id: int) -> TaskPublic:
        """タスク削除"""
        task_repo = TaskRepository()
        deleted_task: task_model = await task_repo.delete(db=db, id=id)
        self._ck_not_found(deleted_task)

        await db.commit()
        return TaskInDB.from_orm(deleted_task)

    def _ck_not_found(self, task: task_model):
        if task is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND, detail="指定されたidのタスクは見つかりませんでした。"
            )

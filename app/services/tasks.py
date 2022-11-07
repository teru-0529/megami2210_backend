#!/usr/bin/python3
# tasks.py

from typing import List

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_404_NOT_FOUND

from app.api.schemas.tasks import TaskCreate, TaskInDB, TaskPublic, TasksQuery
from app.db.models import Task as task_model
from app.db.repositry.tasks import TaskRepository


class TaskService:
    async def create(self, *, db: AsyncSession, new_task: TaskCreate) -> TaskPublic:
        """タスク登録"""
        task = task_model(**new_task.dict())
        task_repo = TaskRepository()
        created_task: task_model = await task_repo.create(db=db, task=task)
        return TaskInDB.from_orm(created_task)

    async def query(self, *, db: AsyncSession) -> TasksQuery:
        """タスク照会"""
        task_repo = TaskRepository()
        query_tasks: List[task_model] = await task_repo.query(db=db)
        tasks: List[TaskPublic] = [TaskInDB.from_orm(task) for task in query_tasks]
        count: int = await task_repo.count(db=db)
        return TasksQuery(tasks=tasks, count=count)

    async def get_by_id(self, *, db: AsyncSession, id: int) -> TaskPublic:
        """タスク取得"""
        task_repo = TaskRepository()
        get_task: task_model = await task_repo.get_by_id(db=db, id=id)
        if not get_task:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND, detail="指定されたidのタスクは見つかりませんでした。"
            )
        return TaskInDB.from_orm(get_task)

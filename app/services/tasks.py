#!/usr/bin/python3
# tasks.py

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_404_NOT_FOUND

from app.api.schemas.tasks import TaskCreate, TaskInDB
from app.db.models import Task as task_model
from app.db.repositry.tasks import TaskRepository


class TaskService:
    async def create(self, *, db: AsyncSession, new_task: TaskCreate) -> TaskInDB:

        task = task_model(**new_task.dict())
        task_repo = TaskRepository()
        created_task = await task_repo.create(db=db, task=task)
        return TaskInDB.from_orm(created_task)

    async def get_by_id(self, *, db: AsyncSession, id: int) -> TaskInDB:

        task_repo = TaskRepository()
        get_task = await task_repo.get_by_id(db=db, id=id)
        if not get_task:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND, detail="指定されたidのタスクは見つかりませんでした。"
            )
        print(get_task)
        return TaskInDB.from_orm(get_task)

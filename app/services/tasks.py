#!/usr/bin/python3
# tasks.py

from app.api.schemas.tasks import TaskCreate, TaskInDB
from app.db.models import Task as task_model
from app.db.repositry.tasks import TaskRepository
from sqlalchemy.ext.asyncio import AsyncSession


class TaskService:
    async def create(self, *, db: AsyncSession, new_task: TaskCreate) -> TaskInDB:

        task = task_model(**new_task.dict())

        task_repo = TaskRepository()
        created_task = await task_repo.create(db=db, task=task)

        return TaskInDB.from_orm(created_task)

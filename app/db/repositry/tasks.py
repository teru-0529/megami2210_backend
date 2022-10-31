#!/usr/bin/python3
# tasks.py

from app.db.models import Task as task_model
from sqlalchemy.ext.asyncio import AsyncSession


class TaskRepository:
    async def create(self, *, db: AsyncSession, task: task_model) -> task_model:

        db.add(task)
        await db.commit()
        await db.refresh(task)
        return task

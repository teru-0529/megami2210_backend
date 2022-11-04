#!/usr/bin/python3
# tasks.py

from typing import Optional, Tuple

from sqlalchemy import select
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Task as task_model


class TaskRepository:
    async def create(self, *, db: AsyncSession, task: task_model) -> task_model:

        db.add(task)
        await db.commit()
        await db.refresh(task)
        return task

    async def get_by_id(self, *, db: AsyncSession, id: int) -> Optional[task_model]:
        result: Result = await db.execute(
            select(task_model).filter(task_model.id == id)
        )
        print(result)
        task: Optional[Tuple[task_model]] = result.first()

        return task[0] if task else None

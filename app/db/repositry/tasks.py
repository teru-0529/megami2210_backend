#!/usr/bin/python3
# tasks.py

from typing import List, Optional, Tuple

from sqlalchemy import literal_column, select, table
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Task as task_model


class TaskRepository:
    async def create(self, *, db: AsyncSession, task: task_model) -> task_model:
        """タスク登録"""
        db.add(task)
        await db.commit()
        await db.refresh(task)
        return task

    async def count(self, *, db: AsyncSession) -> int:
        """タスク件数取得"""
        query = select([literal_column("count(*)")]).select_from(
            table("tasks", schema="todo")
        )
        result: Result = await db.execute(query)
        return result.scalar()

    async def query(self, *, db: AsyncSession) -> List[task_model]:
        """タスク照会"""
        query = select(task_model)
        result: Result = await db.execute(query)
        tasks: List[Tuple[task_model]] = result.all()
        return [tp_task[0] for tp_task in tasks]

    async def get_by_id(self, *, db: AsyncSession, id: int) -> Optional[task_model]:
        """タスク取得"""
        result: Result = await db.execute(
            select(task_model).filter(task_model.id == id)
        )
        task: Optional[Tuple[task_model]] = result.first()
        return task[0] if task else None

#!/usr/bin/python3
# tasks.py

from typing import List, Optional, Tuple

from sqlalchemy import func, select, table
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.tasks import TasksQParam
from app.db.models import Task as task_model
from app.db.query_conf import QueryConf


class TaskRepository:
    async def create(self, *, session: AsyncSession, task: task_model) -> task_model:
        """タスク登録"""
        session.add(task)
        await session.flush()
        return task

    async def update(
        self, *, session: AsyncSession, id: int, patch_params: dict[str, any]
    ) -> Optional[task_model]:
        """タスク更新"""
        base_task = await self.get_by_id(session=session, id=id, for_update=True)
        if base_task is None:
            return None

        # patch_paramsのフィールドを反映
        {
            setattr(base_task, f, v)
            for f, v in patch_params.items()
            if f in base_task.__dict__
        }

        await session.flush()
        return base_task

    async def delete(self, *, session: AsyncSession, id: int) -> Optional[task_model]:
        """タスク削除"""
        base_task = await self.get_by_id(session=session, id=id, for_update=True)
        if base_task is None:
            return None

        await session.delete(base_task)
        await session.flush()
        return base_task

    async def count(self, *, session: AsyncSession, qp: TasksQParam) -> int:
        """タスク件数取得"""
        query = select(func.count())
        if qp.sql():
            query = query.where(*qp.sql())
        else:
            query = query.select_from(table("tasks", schema="todo"))
        result: Result = await session.execute(query)
        return result.scalar()

    async def query(
        self, *, session: AsyncSession, qp: TasksQParam, qc: QueryConf
    ) -> List[task_model]:
        """タスク照会"""
        query = (
            select(task_model)
            .where(*qp.sql())
            .offset(qc.offset)
            .limit(qc.limit)
            .order_by(*qc.order_by)
        )
        result: Result = await session.execute(query)
        tasks: List[Tuple[task_model]] = result.all()
        return [tp_task[0] for tp_task in tasks]

    async def get_by_id(
        self, *, session: AsyncSession, id: int, for_update: bool = False
    ) -> Optional[task_model]:
        """タスク取得"""
        query = select(task_model).filter(task_model.id == id)
        if for_update:
            query = query.with_for_update()
        result: Result = await session.execute(query)
        task: Optional[Tuple[task_model]] = result.first()
        return task[0] if task else None

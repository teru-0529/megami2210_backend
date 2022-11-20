#!/usr/bin/python3
# tasks.py

from typing import List, Optional, Tuple

from sqlalchemy import func, select, table
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.table_models import td_Task
from app.repositries import QueryParam


class TaskRepository:
    async def create(self, *, session: AsyncSession, task: td_Task) -> td_Task:
        """タスク登録"""
        session.add(task)
        await session.flush()
        return task

    async def update(
        self, *, session: AsyncSession, id: int, patch_params: dict[str, any]
    ) -> Optional[td_Task]:
        """タスク更新"""
        base_task: td_Task = await self.get_by_id(
            session=session, id=id, for_update=True
        )
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

    async def delete(self, *, session: AsyncSession, id: int) -> Optional[td_Task]:
        """タスク削除"""
        base_task: td_Task = await self.get_by_id(
            session=session, id=id, for_update=True
        )
        if base_task is None:
            return None

        await session.delete(base_task)
        await session.flush()
        return base_task

    async def count(self, *, session: AsyncSession, query_param: QueryParam) -> int:
        """タスク件数取得"""
        query = select(func.count())
        if query_param.filter:
            query = query.where(*query_param.filter)
        else:
            query = query.select_from(table("tasks", schema="todo"))
        result: Result = await session.execute(query)
        return result.scalar()

    async def query(
        self, *, session: AsyncSession, query_param: QueryParam
    ) -> List[td_Task]:
        """タスク照会"""
        query = (
            select(td_Task)
            .where(*query_param.filter)
            .offset(query_param.offset)
            .limit(query_param.limit)
            .order_by(*query_param.sort)
        )
        result: Result = await session.execute(query)
        tasks: List[Tuple[td_Task]] = result.all()
        return [tp_task[0] for tp_task in tasks]

    async def get_by_id(
        self, *, session: AsyncSession, id: int, for_update: bool = False
    ) -> Optional[td_Task]:
        """タスク取得"""
        query = select(td_Task).filter(td_Task.id == id)
        if for_update:
            query = query.with_for_update()
        result: Result = await session.execute(query)
        task: Optional[Tuple[td_Task]] = result.first()
        return task[0] if task else None

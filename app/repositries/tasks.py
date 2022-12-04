#!/usr/bin/python3
# tasks.py

from typing import List, Optional, Tuple

from sqlalchemy import func, select, table
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.table_models import td_Task, ac_Profile
from app.repositries import QueryParam

# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class TaskRepository:

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    async def create(self, *, session: AsyncSession, task: td_Task) -> td_Task:
        """タスク登録"""
        session.add(task)
        await session.flush()
        return task

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    async def update(
        self, *, session: AsyncSession, id: int, patch_params: dict[str, any]
    ) -> Optional[td_Task]:
        """タスク更新"""
        result: td_Task = await self.get_by_id(session=session, id=id, for_update=True)
        if result is None:
            return None

        base_task = result[0]
        # patch_paramsのフィールドを反映
        {
            setattr(base_task, f, v)
            for f, v in patch_params.items()
            if f in base_task.__dict__
        }

        await session.flush()
        return base_task

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    async def delete(self, *, session: AsyncSession, id: int) -> Optional[td_Task]:
        """タスク削除"""
        result: td_Task = await self.get_by_id(session=session, id=id, for_update=True)
        if result is None:
            return None

        base_task = result[0]
        await session.delete(base_task)
        await session.flush()
        return base_task

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    async def count(self, *, session: AsyncSession, query_param: QueryParam) -> int:
        """タスク件数取得"""
        query = select(func.count())
        if query_param.filter:
            query = query.where(*query_param.filter)
        else:
            query = query.select_from(table("tasks", schema="todo"))
        result: Result = await session.execute(query)
        return result.scalar()

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    async def search(
        self,
        *,
        session: AsyncSession,
        query_param: QueryParam,
        inclide_account: bool = False
    ) -> List[Tuple[td_Task, ac_Profile, ac_Profile]]:
        """タスク検索"""
        if inclide_account:
            registrant = aliased(ac_Profile)
            asaignee = aliased(ac_Profile)
            query = (
                select(td_Task, registrant, asaignee)
                .outerjoin(registrant, td_Task.registrant_id == registrant.account_id)
                .outerjoin(asaignee, td_Task.asaignee_id == asaignee.account_id)
            )
        else:
            query = select(td_Task)
        query = (
            query.where(*query_param.filter)
            .offset(query_param.offset)
            .limit(query_param.limit)
            .order_by(*query_param.sort)
        )

        result: Result = await session.execute(query)
        return result.all()

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    async def get_by_id(
        self,
        *,
        session: AsyncSession,
        id: int,
        for_update: bool = False,
        inclide_account: bool = False
    ) -> Optional[Tuple[td_Task, ac_Profile, ac_Profile]]:
        """タスク取得"""
        if inclide_account:
            registrant = aliased(ac_Profile)
            asaignee = aliased(ac_Profile)
            query = (
                select(td_Task, registrant, asaignee)
                .outerjoin(registrant, td_Task.registrant_id == registrant.account_id)
                .outerjoin(asaignee, td_Task.asaignee_id == asaignee.account_id)
            )
        else:
            query = select(td_Task)
        query = query.filter(td_Task.id == id)
        if for_update:
            query = query.with_for_update()
        result: Result = await session.execute(query)
        return result.first()

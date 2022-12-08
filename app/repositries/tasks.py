#!/usr/bin/python3
# tasks.py

from typing import List, Optional, Tuple

from sqlalchemy import func, select, table
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.table_models import ac_Profile, td_Task, td_Watcher
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

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    async def create_watcher(
        self, *, session: AsyncSession, watcher: td_Watcher
    ) -> None:
        """監視タスク登録"""

        # UPSERT
        stmt = """
        INSERT INTO todo.watcher (watcher_id, task_id, note)
        VALUES ('{0}', {1}, '{2}')
        ON CONFLICT (watcher_id, task_id)
        DO UPDATE SET note = '{2}';
        """.format(
            watcher.watcher_id, watcher.task_id, watcher.note
        )

        await session.execute(stmt)
        await session.flush()

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    async def delete_watcher(
        self, *, session: AsyncSession, watcher_id: str, task_id: int
    ) -> bool:
        """監視タスク削除"""

        base_task = await self.get_by_id(session=session, id=task_id)
        if not base_task:
            return False

        query = select(td_Watcher).filter(
            td_Watcher.watcher_id == watcher_id, td_Watcher.task_id == task_id
        )
        result: Result = await session.execute(query)
        base_watcher = result.first()
        if base_watcher is None:
            return True

        base_watcher = base_watcher[0]
        await session.delete(base_watcher)
        await session.flush()
        return True

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    async def get_watch_tasks(
        self, *, session: AsyncSession, watcher_id: str
    ) -> List[Tuple[td_Watcher, td_Task]]:
        """監視タスク検索"""

        query = (
            select(td_Watcher, td_Task)
            .outerjoin(td_Watcher, td_Watcher.task_id == td_Task.id)
            .filter(td_Watcher.watcher_id == watcher_id)
            .order_by("task_id")
        )
        result: Result = await session.execute(query)
        return result.all()

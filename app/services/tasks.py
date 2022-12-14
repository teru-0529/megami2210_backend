#!/usr/bin/python3
# tasks.py

from typing import List, Tuple, Union

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from app.api.schemas.accounts import ProfileInDB
from app.api.schemas.tasks import (
    TaskCreate,
    TaskFilter,
    TaskInDB,
    TaskPublic,
    TaskPublicList,
    TaskUpdate,
    TaskWithAccount,
)
from app.models.table_models import ac_Profile, td_Task
from app.repositries import QueryParam
from app.repositries.tasks import TaskRepository
from app.services import auth_service

# 対象無し例外
not_found_exception: HTTPException = HTTPException(
    status_code=HTTP_404_NOT_FOUND,
    detail="Task resource not found by specified Id.",
)

# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class TaskService:

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    async def create(
        self, *, session: AsyncSession, token: str, new_task: TaskCreate
    ) -> TaskPublic:
        """タスク登録"""
        account_id = auth_service.get_id_from_token(token=token)
        task = td_Task(**new_task.dict())
        task.registrant_id = account_id
        repo = TaskRepository()
        try:
            created_task: td_Task = await repo.create(session=session, task=task)
            await session.commit()
        except IntegrityError as e:
            await session.rollback()
            self.ch_exception_detail(e)

        await session.refresh(created_task)
        return TaskInDB.from_orm(created_task)

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    async def search(
        self,
        offset: int,
        limit: int,
        sort: str,
        sub_resources: str,
        *,
        session: AsyncSession,
        filter: TaskFilter
    ) -> TaskPublicList:
        """タスク照会"""
        inclide_account = (
            "account" in sub_resources.split(",") if sub_resources else False
        )

        query_param = self.New_QueryParam(
            offset=offset, limit=limit, sort=sort, filter=filter
        )
        repo = TaskRepository()
        searched_tasks: List[
            Tuple[td_Task, ac_Profile, ac_Profile]
        ] = await repo.search(
            session=session, query_param=query_param, inclide_account=inclide_account
        )
        tasks: List[Union[TaskInDB, TaskWithAccount]] = [
            self.result(task, inclide_account).dict() for task in searched_tasks
        ]
        count: int = await repo.count(session=session, query_param=query_param)
        # ※リスト要素が可変の場合にdictに変換してから投入する必要がある（要確認）
        result = TaskPublicList(tasks=[], count=count)
        result = result.copy(update={"tasks": tasks})
        return result

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    async def get_by_id(
        self, sub_resources: str, *, session: AsyncSession, id: int
    ) -> Union[TaskPublic, TaskWithAccount]:
        """タスク取得"""
        inclide_account = (
            "account" in sub_resources.split(",") if sub_resources else False
        )

        repo = TaskRepository()
        task: td_Task = await repo.get_by_id(
            session=session, id=id, inclide_account=inclide_account
        )
        if not task:
            raise not_found_exception

        return self.result(task, inclide_account)

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    async def patch(
        self, *, session: AsyncSession, id: int, patch_params: TaskUpdate
    ) -> TaskPublic:
        """タスク更新"""
        update_dict = patch_params.dict(exclude_unset=True)
        repo = TaskRepository()
        try:
            updated_task: td_Task = await repo.update(
                session=session, id=id, patch_params=update_dict
            )
        except IntegrityError as e:
            await session.rollback()
            self.ch_exception_detail(e)
        if not updated_task:
            await session.rollback()
            raise not_found_exception

        await session.commit()
        await session.refresh(updated_task)
        return TaskInDB.from_orm(updated_task)

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    async def delete(self, *, session: AsyncSession, id: int) -> TaskPublic:
        """タスク削除"""
        repo = TaskRepository()
        deleted_task: td_Task = await repo.delete(session=session, id=id)
        if not deleted_task:
            await session.rollback()
            raise not_found_exception

        await session.commit()
        return TaskInDB.from_orm(deleted_task)

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----
    # [INNER]クエリパラメータクラスの作成
    def New_QueryParam(
        self, *, offset: int, limit: int, sort: str, filter: TaskFilter
    ) -> QueryParam:
        try:
            queryParm = QueryParam(
                columns=td_Task.__table__.columns,
                offset=offset,
                limit=limit,
                sort=sort,
                default_key="+id",
            )
        except ValueError as e:
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail=e.args
            )
        if filter.title_cn is not None:
            queryParm.append_filter(td_Task.title.contains(filter.title_cn))
        if filter.description_cn is not None:
            queryParm.append_filter(td_Task.description.contains(filter.description_cn))
        if filter.asaignee_id_in is not None:
            queryParm.append_filter(td_Task.asaignee_id.in_(filter.asaignee_id_in))
        if filter.asaignee_id_ex is True:
            queryParm.append_filter(td_Task.asaignee_id.is_not(None))
        if filter.asaignee_id_ex is False:
            queryParm.append_filter(td_Task.asaignee_id.is_(None))
        if filter.status_in is not None:
            queryParm.append_filter(td_Task.status.in_(filter.status_in))
        if filter.is_significant_eq is not None:
            queryParm.append_filter(
                td_Task.is_significant.is_(filter.is_significant_eq)
            )
        if filter.deadline_from is not None:
            queryParm.append_filter(td_Task.deadline >= filter.deadline_from)
        if filter.deadline_to is not None:
            queryParm.append_filter(td_Task.deadline <= filter.deadline_to)
        return queryParm

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----
    # [INNER]例外文字列の判定
    def ch_exception_detail(self, e: IntegrityError) -> None:
        args = e.orig.args[0]
        if self.exists_params(
            args,
            [
                "asyncpg.exceptions.ForeignKeyViolationError",
                "violates foreign key constraint",
                "fk_asaignee_id",
            ],
        ):
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="violates foreign key constraint: [fk_asaignee_id].",
            )
        raise e  # pragma: no cover

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----
    # [INNER]例外文字列の判定（指定文字列を含むか否か）
    def exists_params(self, args: str, params: List[str]) -> bool:
        filtered = [x for x in params if x in args]
        return filtered == params

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----
    # [INNER]検索結果からレスポンスモデルを構築する
    def result(
        self, task: Tuple[td_Task, ac_Profile, ac_Profile], inclide_account: bool
    ) -> Union[TaskPublic, TaskWithAccount]:
        if inclide_account:
            result = TaskWithAccount.from_orm(task[0])
            result.registrant = ProfileInDB.from_orm(task[1]) if task[1] else None
            result.asaignee = ProfileInDB.from_orm(task[2]) if task[2] else None
            return result
        else:
            return TaskInDB.from_orm(task[0])

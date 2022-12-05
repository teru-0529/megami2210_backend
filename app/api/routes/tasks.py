#!/usr/bin/python3
# tasks.py
# TODO:watcher

from typing import Union

from fastapi import APIRouter, Body, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_201_CREATED

from app.api.routes.mine import oauth2_scheme
from app.api.schemas.base import Message, q_limit, q_offset, q_sort
from app.api.schemas.tasks import (
    TaskCreate,
    TaskFilter,
    TaskPublic,
    TaskPublicList,
    TaskWithAccount,
    TaskUpdate,
    p_task_id,
    q_sub_resources,
)
from app.core.database import get_session
from app.services.permittion import CkPermission
from app.services.tasks import TaskService

router = APIRouter()

# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


@router.post(
    "/",
    response_model=TaskPublic,
    name="tasks:create",
    response_description="Create new task successful",
    status_code=HTTP_201_CREATED,
)
async def create(
    request: Request,
    response: Response,
    new_task: TaskCreate = Body(...),
    session: AsyncSession = Depends(get_session),
    token: str = Depends(oauth2_scheme),
) -> TaskPublic:
    """
    タスクの新規作成。</br>
    PROVISIONALユーザーは実行不可。</br>
    登録時、**id**は自動採番、**registrant_id**はログインユーザーのIDを設定、**status**は`TODO`固定値。

    [BODY]

    - **title**: タスクの名称[reqired]
    - **description**: タスクの詳細内容
    - **asaignee_id**: タスクの担当者
    - **is_significant**: 重要タスクの場合にTrue[default=false]
    - **deadline**: タスク期限日(YYYY-MM-DD) ※当日以降の日付を指定可能
    """
    checker = CkPermission(session=session, token=token)
    await checker.activate_and_upper_general()

    service = TaskService()
    created_task = await service.create(session=session, token=token, new_task=new_task)
    response.headers["Location"] = request.url_for("tasks:get", id=created_task.id)
    return created_task


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


@router.post(
    "/search",
    tags=["search"],
    name="tasks:search",
    responses={
        200: {
            "model": TaskPublicList,
            "description": "Search tasks successful",
        },
    },
)
async def search(
    offset: int = q_offset,
    limit: int = q_limit,
    sort: str = q_sort(default="+id", example="+deadline,-id"),
    sub_resources: str = q_sub_resources,
    filter: TaskFilter = Body(...),
    session: AsyncSession = Depends(get_session),
    token: str = Depends(oauth2_scheme),
) -> TaskPublicList:
    """
    タスク検索。</br>
    アクティベート後のすべてのユーザーが実行可能。</br>
    ※QUERYメソッドが提案されているが現状未実装のため、POSTメソッド、サブリソースを利用した対応

    [QUERY]

    - **offset**: 結果抽出時のオフセット値[default=0]
    - **limit**: 結果抽出時の最大件数[default=10] ※1システム制限として最大1000件まで指定可能
    - **sort**: ソートキー[default=+id] ※2[+deadline,-asaignee_id] のように複数指定可能。+:ASC、-:DESC
        - 指定可能キー: `id`, `title`, `description`, `asaignee_id`, `status`, `is_significant`, `deadline`
    - **sub-resources**: レスポンスに含めるサブリソース
        - 指定可能キー: `account`…「登録者」「担当者」サブリソースをレスポンスに含める。

    [BODY]

    - **title_cn**: <クエリ条件> タスクの名称[CONTAINS]
    - **description_cn**: <クエリ条件> タスク詳細[CONTAINS]
    - **asaignee_id_in**: <クエリ条件> タスク担当者[IN] ※3「asaignee_id_in」「asaignee_id_ex」はいずれか一方のみ指定可能
    - **asaignee_id_ex**: <クエリ条件> タスク担当者[EXIST] ※3
    - **status_in**: <クエリ条件> タスクステータス[IN]
    - **is_significant_eq**: <クエリ条件> 重要フラグ[EQUAL]
    - **deadline_from**: <クエリ条件> タスク期限[FROM] ※4「deadline_from」<=「deadline_to」を保つ必要がある
    - **deadline_to**: <クエリ条件> タスク期限[TO] ※4
    """
    checker = CkPermission(session=session, token=token)
    await checker.activate_only()

    service = TaskService()
    tasks = await service.search(
        offset, limit, sort, sub_resources, session=session, filter=filter
    )
    return tasks


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


@router.get(
    "/{id}/",
    name="tasks:get",
    responses={
        404: {
            "model": Message,
            "description": "Resource not found Error",
            "content": {
                "application/json": {"example": {"detail": "Resource not found."}}
            },
        },
        200: {
            "model": Union[TaskPublic, TaskWithAccount],
            "description": "Get task successful",
        },
    },
)
async def get(
    id: int = p_task_id,
    sub_resources: str = q_sub_resources,
    session: AsyncSession = Depends(get_session),
    token: str = Depends(oauth2_scheme),
) -> Union[TaskPublic, TaskWithAccount]:
    """
    タスク1件の取得。</br>
    アクティベート後のすべてのユーザーが実行可能。

    [PATH]

    - **id**: タスクID[reqired]

    [QUERY]

    - **sub-resources**: レスポンスに含めるサブリソース
        - 指定可能キー: `account`…「登録者」「担当者」サブリソースをレスポンスに含める。
    """
    checker = CkPermission(session=session, token=token)
    await checker.activate_only()

    service = TaskService()
    task = await service.get_by_id(sub_resources, session=session, id=id)
    return task


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


@router.patch(
    "/{id}/",
    name="tasks:patch",
    responses={
        404: {
            "model": Message,
            "description": "Resource not found Error",
            "content": {
                "application/json": {"example": {"detail": "Resource not found."}}
            },
        },
        200: {"model": TaskPublic, "description": "Update task successful"},
    },
)
async def patch(
    id: int = p_task_id,
    patch_params: TaskUpdate = Body(...),
    session: AsyncSession = Depends(get_session),
    token: str = Depends(oauth2_scheme),
) -> TaskPublic:
    """
    タスク1件の更新。</br>
    PROVISIONALユーザーは実行不可。</br>
    **title**、**is_significant** は変更できない。

    [PATH]

    - **id**: タスクID[reqired]

    [BODY]

    - **description**: タスクの詳細内容
    - **asaignee_id**: タスクの担当者
    - **status**: タスクステータス
    - **deadline**: タスク期限日(YYYY-MM-DD) ※当日以降の日付を指定可能
    """
    checker = CkPermission(session=session, token=token)
    await checker.activate_and_upper_general()

    service = TaskService()
    task = await service.patch(session=session, id=id, patch_params=patch_params)
    return task


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


@router.delete(
    "/{id}/",
    name="tasks:delete",
    responses={
        404: {
            "model": Message,
            "description": "Resource not found Error",
            "content": {
                "application/json": {"example": {"detail": "Resource not found."}}
            },
        },
        200: {"model": TaskPublic, "description": "Delete task successful"},
    },
)
async def delete(
    id: int = p_task_id,
    session: AsyncSession = Depends(get_session),
    token: str = Depends(oauth2_scheme),
) -> TaskPublic:
    """
    タスク1件の削除。</br>
    PROVISIONALユーザーは実行不可。

    [PATH]

    - **id**: タスクID[reqired]

    """
    checker = CkPermission(session=session, token=token)
    await checker.activate_and_upper_general()

    service = TaskService()
    task = await service.delete(session=session, id=id)
    return task

#!/usr/bin/python3
# tasks.py

from fastapi import APIRouter, Body, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_200_OK, HTTP_201_CREATED

from app.api.schemas.base import Message, q_limit, q_offset, q_sort
from app.api.schemas.tasks import (
    TaskCreate,
    TaskPublic,
    TasksQuery,
    p_id,
    q_exclude_asaignee,
)
from app.db.database import get_db
from app.services.tasks import TaskService

router = APIRouter()


@router.post(
    "/",
    response_model=TaskPublic,
    name="tasks:create",
    response_description="Creat New Task",
    status_code=HTTP_201_CREATED,
)
async def create_task(
    request: Request,
    response: Response,
    new_task: TaskCreate = Body(...),
    db: AsyncSession = Depends(get_db),
) -> TaskPublic:
    """
    タスクの新規作成。</br>
    登録時、**id**は自動採番、**status**は`TODO`固定。:

    [BODY]

    - **title**: タスクの名称[Reqired]
    - **description**: タスクの詳細内容
    - **asaignee_id**: タスクの担当者
    - **is_significant**: 重要タスクの場合にTrue[Default=false]
    - **deadline**: タスク期限日(YYYY-MM-DD) ※当日以降の日付を指定可能
    """

    service = TaskService()
    created_task = await service.create(db=db, new_task=new_task)
    response.headers["Location"] = request.url_for(
        "tasks:get-by-id", id=created_task.id
    )
    return created_task


@router.post(
    "/be-queried",
    response_model=TasksQuery,
    name="tasks:query",
    response_description="query Tasks",
    status_code=HTTP_200_OK,
)
async def quert_tasks(
    request: Request,  # TODO:
    response: Response,  # TODO:
    offset: int = q_offset,  # TODO:
    limit: int = q_limit,  # TODO:
    sort: str = q_sort,  # TODO:
    execute_assaignee: bool = q_exclude_asaignee,  # TODO:
    # new_task: TaskCreate = Body(...),# TODO:
    db: AsyncSession = Depends(get_db),
) -> TaskPublic:
    """
    タスク検索。</br>
    ※QUERYメソッドが提案されているが現状未実装のため、POSTメソッド、サブリソースを利用した対応

    [QUERY]

    - **offset**: 結果抽出時のオフセット値[Default=0]
    - **limit**: 結果抽出時の最大件数[Default=10]
    - **sort**: ソートキー[Default=+id] ※[+deadline,-asaignee_id] のように複数指定可能。+:ASC、-:DESC
    - **exclude_asaignee**: 担当者情報の詳細情報をレスポンスから除外する場合にTrue[Default=false]

    [BODY]

    - **query**: 検索条件 ※TODO:
    """
    service = TaskService()
    query_task = await service.query(db=db)
    return query_task


@router.get(
    "/{id}/",
    response_model=TaskPublic,
    name="tasks:get-by-id",
    status_code=HTTP_200_OK,
    responses={
        404: {
            "model": Message,
            "description": "The task was not found",
            "content": {"application/json": {"example": {"message": "リソースが存在しません。"}}},
        },
        200: {"description": "Task requested by ID", "model": TaskPublic},
    },
)
async def get_task_by_id(
    id: int = p_id,
    db: AsyncSession = Depends(get_db),
) -> TaskPublic:
    """
    タスクの1件取得。</br>

    [PATH]

    - **id**: タスクID[Reqired]
    """
    service = TaskService()
    task = await service.get_by_id(db=db, id=id)
    return task

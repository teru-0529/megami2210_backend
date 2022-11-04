#!/usr/bin/python3
# tasks.py

from fastapi import APIRouter, Body, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_200_OK, HTTP_201_CREATED

from app.api.schemas.base import Message
from app.api.schemas.tasks import TaskCreate, TaskPublic
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
    - **is_significant**: 重要タスクの場合にTrue[Default=False]
    - **deadline**: タスク期限日(YYYY-MM-DD) ※当日以降の日付を指定可能
    """
    service = TaskService()
    created_task = await service.create(db=db, new_task=new_task)
    return created_task


@router.get(
    "/{id}/",
    response_model=TaskPublic,
    name="tasks:get-by-id",
    # response_description="Get Task",
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
    id: int,
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

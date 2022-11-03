#!/usr/bin/python3
# tasks.py

import logging

from app.api.schemas.tasks import TaskCreate, TaskPublic
from app.db.database import get_db
from app.services.tasks import TaskService
from fastapi import APIRouter, Body, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_201_CREATED

logger = logging.getLogger(__file__)

router = APIRouter()


@router.post(
    "/",
    response_model=TaskPublic,
    name="tasks:create",
    response_description="Created New Task",
    status_code=HTTP_201_CREATED,
)
async def create_task(
    db: AsyncSession = Depends(get_db),
    new_task: TaskCreate = Body(...),
) -> TaskPublic:
    """
    タスクの新規作成。</br>
    登録時、**id**は自動採番、**status**は`TODO`固定。:

    - **title**: タスクの名称[Reqired]
    - **description**: タスクの詳細内容
    - **asaignee_id**: タスクの担当者
    - **is_significant**: 重要タスクの場合にTrue[Default=False]
    - **deadline**: タスク期限日(YYYY-MM-DD) ※当日以降の日付を指定可能
    """
    service = TaskService()
    created_task = await service.create(db=db, new_task=new_task)
    return created_task

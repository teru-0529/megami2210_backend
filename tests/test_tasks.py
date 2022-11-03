#!/usr/bin/python3
# test_tasks.py

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from starlette.status import (
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_201_CREATED,
)
from app.api.schemas.tasks import TaskCreate
from datetime import date

pytestmark = pytest.mark.asyncio


class TestTasksRoutes:
    async def test_create_route_exist(self, app: FastAPI, client: AsyncClient) -> None:
        """ルートの存在チェック"""
        res = await client.post(app.url_path_for("tasks:create"), json={})
        assert res.status_code != HTTP_404_NOT_FOUND

    @pytest.mark.skip
    async def test_invalid_input_raises_error(
        self, app: FastAPI, client: AsyncClient
    ) -> None:
        """空のJsonを入れたときにバリデーションエラー"""
        res = await client.post(app.url_path_for("tasks:create"), json={})
        assert res.status_code == HTTP_422_UNPROCESSABLE_ENTITY


class TestCreateTask:

    # 正常ケースパラメータ
    valid_params = {
        "全項目": TaskCreate(
            title="test task",
            description="test description",
            asaignee_id="100",
            is_significant=True,
            deadline=date(2050, 12, 31),
        ),
        "<担当者>除く": TaskCreate(
            title="test task",
            description="テストタスク",
            is_significant=True,
            deadline=date(2050, 12, 31),
        ),
        "<重要タスク>除く": TaskCreate(
            title="test task",
            description="test description",
            asaignee_id="100",
            deadline=date(2050, 12, 31),
        ),
        "<期限>除く": TaskCreate(
            title="test task",
            description="test description",
            asaignee_id="100",
            is_significant=False,
        ),
    }

    @pytest.mark.parametrize(
        "new_task", list(valid_params.values()), ids=list(valid_params.keys())
    )
    async def test_valid_input(
        self,
        app: FastAPI,
        client: AsyncClient,
        new_task: TaskCreate,
    ) -> None:

        res = await client.post(
            app.url_path_for("tasks:create"),
            data=new_task.json(exclude_unset=True),
        )
        print(new_task.json(exclude_unset=True))
        assert res.status_code == HTTP_201_CREATED
        print(res.json())
        created_task = TaskCreate(**res.json())
        assert created_task == new_task

    # 異常ケースパラメータ
    invalid_params = {
        "ペイロードなし": ("{}", HTTP_422_UNPROCESSABLE_ENTITY),
        "<名称>：必須": ('{"description":"dummy"}', HTTP_422_UNPROCESSABLE_ENTITY),
        "<名称>：桁数超過": (
            '{"description":"000000000100000000010000000001000000001"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<担当者>：桁数不足": (
            '{"title":"dummy","asaignee_id":"10"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<担当者>：桁数超過": (
            '{"title":"dummy","asaignee_id":"0000"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<重要タスク>：型違い": (
            '{"title":"dummy","is_significant":10}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<期限>：型違い": ('{"title":"dummy","deadline":10}', HTTP_422_UNPROCESSABLE_ENTITY),
        "<期限>：過去日付": (
            '{"title":"dummy","deadline": "2000-12-31"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
    }

    @pytest.mark.parametrize(
        "param", list(invalid_params.values()), ids=list(invalid_params.keys())
    )
    async def test_invalid_input(
        self,
        app: FastAPI,
        client: AsyncClient,
        param: tuple[str, int],
    ) -> None:
        res = await client.post(
            app.url_path_for("tasks:create"),
            data=param[0],
        )
        assert res.status_code == param[1]

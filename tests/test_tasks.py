#!/usr/bin/python3
# test_tasks.py

from datetime import date

from pandas import read_csv, DataFrame
import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.routing import NoMatchFound
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from app.api.schemas.tasks import TaskCreate, TaskInDB, TasksQuery
from app.services.tasks import TaskService

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def tmp_task(async_db: AsyncSession) -> TaskInDB:
    new_task = TaskCreate(
        title="tmp task",
    )
    service = TaskService()
    created_task = await service.create(db=async_db, new_task=new_task)
    return created_task


@pytest.fixture
def import_task(sync_engine: Engine) -> DataFrame:
    datas: DataFrame = read_csv("tests/data/test_task_data.csv", encoding="utf-8")
    datas.to_sql(
        name="tasks", con=sync_engine, schema="todo", if_exists="replace", index=False
    )
    return datas


class TestTasksRoutes:
    async def test_create_route_exist(self, app: FastAPI, client: AsyncClient) -> None:
        try:
            await client.post(app.url_path_for("tasks:create"), json={})
        except NoMatchFound:
            pytest.fail("route not exist")

    async def test_get_route_exist(self, app: FastAPI, client: AsyncClient) -> None:
        try:
            await client.get(app.url_path_for("tasks:get-by-id", id=1))
        except NoMatchFound:
            pytest.fail("route not exist")

    # @pytest.mark.skip
    async def test_list_route_exist(self, app: FastAPI, client: AsyncClient) -> None:
        try:
            await client.get(app.url_path_for("tasks:query"))
        except NoMatchFound:
            pytest.fail("route not exist")


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
        self, app: FastAPI, client: AsyncClient, new_task: TaskCreate
    ) -> None:

        res = await client.post(
            app.url_path_for("tasks:create"),
            data=new_task.json(exclude_unset=True),
        )
        assert res.status_code == HTTP_201_CREATED
        created_task = TaskCreate(**res.json())
        assert created_task == new_task

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


class TestGetTask:
    async def test_valid_input(
        self, app: FastAPI, client: AsyncClient, tmp_task: TaskInDB
    ) -> None:

        res = await client.get(app.url_path_for("tasks:get-by-id", id=tmp_task.id))
        assert res.status_code == HTTP_200_OK
        get_task = TaskInDB(**res.json())
        assert get_task == tmp_task

    # 異常ケースパラメータ
    invalid_params = {
        "<ID>範囲外（500）": (500, HTTP_404_NOT_FOUND),
        "<ID>範囲外（-1）": (
            -1,
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<ID>型違い": (
            "ABC",
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<ID>None": (None, HTTP_422_UNPROCESSABLE_ENTITY),
    }

    @pytest.mark.parametrize(
        "param", list(invalid_params.values()), ids=list(invalid_params.keys())
    )
    async def test_invalid_input(
        self,
        app: FastAPI,
        client: AsyncClient,
        param: tuple[any, int],
    ) -> None:
        res = await client.get(app.url_path_for("tasks:get-by-id", id=param[0]))
        assert res.status_code == param[1]


class TestQueryTask:
    async def test_valid_input(
        self, app: FastAPI, client: AsyncClient, import_task: DataFrame
    ) -> None:

        res = await client.post(app.url_path_for("tasks:query"), data="{}")
        assert res.status_code == HTTP_200_OK
        result = TasksQuery(**res.json())
        # 取得件数
        assert result.count == len(import_task)

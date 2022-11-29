#!/usr/bin/python3
# test_tasks.py

from datetime import date
from typing import List

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient
from pandas import DataFrame, read_csv
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.types import DATE
from starlette.routing import NoMatchFound
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from app.api.schemas.tasks import TaskCreate, TaskInDB, TaskPublicList, TaskUpdate
from app.models.segment_values import TaskStatus
from app.services.tasks import TaskService

pytestmark = pytest.mark.asyncio
is_regression = True


@pytest_asyncio.fixture
async def fixed_task(session: AsyncSession) -> TaskInDB:
    new_task = TaskCreate(
        title="fixed task",
        description="fixed task",
        asaignee_id="T-001",
        deadline=date(2030, 12, 31),
    )
    service = TaskService()
    created_task = await service.create(session=session, new_task=new_task)
    yield created_task
    await service.delete(session=session, id=created_task.id)


@pytest_asyncio.fixture
async def task_for_update(session: AsyncSession) -> TaskInDB:
    new_task = TaskCreate(
        title="updated task",
        description="updated task",
        asaignee_id="T-001",
        deadline=date(2030, 12, 31),
    )
    service = TaskService()
    created_task = await service.create(session=session, new_task=new_task)
    yield created_task
    await service.delete(session=session, id=created_task.id)


@pytest_asyncio.fixture
async def task_for_delete(session: AsyncSession) -> TaskInDB:
    new_task = TaskCreate(
        title="updated task",
        description="updated task",
        asaignee_id="T-001",
        deadline=date(2030, 12, 31),
    )
    service = TaskService()
    created_task = await service.create(session=session, new_task=new_task)
    return created_task


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


@pytest.fixture
def import_task(s_engine: Engine) -> DataFrame:
    datas: DataFrame = read_csv(
        "tests/data/test_task_data.csv", encoding="utf-8", dtype={3: str}
    )
    datas.to_sql(
        name="tasks",
        con=s_engine,
        schema="todo",
        if_exists="append",
        index=False,
        dtype={"deadline": DATE},
    )
    return datas


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


@pytest.mark.skipif(not is_regression, reason="not regression phase")
class TestRouteExists:
    async def test_create_route(self, app: FastAPI, client: AsyncClient) -> None:
        try:
            await client.post(app.url_path_for("tasks:create"), json={})
        except NoMatchFound:
            pytest.fail("route not exist")

    async def test_get_route(self, app: FastAPI, client: AsyncClient) -> None:
        try:
            await client.get(app.url_path_for("tasks:get", id=1))
        except NoMatchFound:
            pytest.fail("route not exist")

    async def test_query_route(self, app: FastAPI, client: AsyncClient) -> None:
        try:
            await client.get(app.url_path_for("tasks:query"))
        except NoMatchFound:
            pytest.fail("route not exist")

    async def test_patch_route(self, app: FastAPI, client: AsyncClient) -> None:
        try:
            await client.get(app.url_path_for("tasks:patch", id=1))
        except NoMatchFound:
            pytest.fail("route not exist")

    async def test_delete_route(self, app: FastAPI, client: AsyncClient) -> None:
        try:
            await client.get(app.url_path_for("tasks:delete", id=1))
        except NoMatchFound:
            pytest.fail("route not exist")


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


@pytest.mark.skipif(not is_regression, reason="not regression phase")
class TestCreate:

    # 正常ケースパラメータ
    valid_params = {
        "<body:full>": TaskCreate(
            title="test task",
            description="test description",
            asaignee_id="T-001",
            is_significant=True,
            deadline=date(2050, 12, 31),
        ),
        "<body:asaignee_id>:任意入力": TaskCreate(
            title="test task",
            description="テストタスク",
            is_significant=True,
            deadline=date(2050, 12, 31),
        ),
        "<body:is_significant>デフォルト値": TaskCreate(
            title="test task",
            description="test description",
            asaignee_id="T-001",
            deadline=date(2050, 12, 31),
        ),
        "<body:deadline>:任意入力": TaskCreate(
            title="test task",
            description="test description",
            asaignee_id="T-001",
            is_significant=False,
        ),
    }

    @pytest.mark.parametrize(
        "new_task", list(valid_params.values()), ids=list(valid_params.keys())
    )
    async def test_ok_case(
        self, app: FastAPI, client: AsyncClient, new_task: TaskCreate
    ) -> None:

        res = await client.post(
            app.url_path_for("tasks:create"),
            data=new_task.json(exclude_unset=True),
        )
        assert res.status_code == HTTP_201_CREATED
        created_task = TaskInDB(**res.json())
        assert created_task.title == new_task.title
        assert created_task.description == new_task.description
        assert created_task.asaignee_id == new_task.asaignee_id
        assert created_task.is_significant == new_task.is_significant
        assert created_task.deadline == new_task.deadline

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    # 異常ケースパラメータ
    invalid_params = {
        "<body:None>": ("{}", HTTP_422_UNPROCESSABLE_ENTITY),
        "<body:title>:必須": ('{"description":"dummy"}', HTTP_422_UNPROCESSABLE_ENTITY),
        "<body:title>:桁数超過": (
            '{"title":"000000000100000000010000000001000000001"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:asaignee_id>:桁数不足": (
            '{"title":"dummy","asaignee_id":"10"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:asaignee_id>:桁数超過": (
            '{"title":"dummy","asaignee_id":"000000"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:is_significant>:型不正": (
            '{"title":"dummy","is_significant":10}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:deadline>:型不正": (
            '{"title":"dummy","deadline":10}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:deadline>:過去日付": (
            '{"title":"dummy","deadline": "2000-12-31"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body>:未定義フィールド": (
            '{"title":"dummy","dummy":"dummy"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body>:None": (
            None,
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
    }

    @pytest.mark.parametrize(
        "param", list(invalid_params.values()), ids=list(invalid_params.keys())
    )
    async def test_ng_case(
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


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


@pytest.mark.skipif(not is_regression, reason="not regression phase")
class TestGet:
    async def test_ok_case(
        self, app: FastAPI, client: AsyncClient, fixed_task: TaskInDB
    ) -> None:

        res = await client.get(app.url_path_for("tasks:get", id=fixed_task.id))
        assert res.status_code == HTTP_200_OK
        get_task = TaskInDB(**res.json())
        assert get_task == fixed_task

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    # 異常ケースパラメータ
    invalid_params = {
        "<path:id>:存在しない": (500, HTTP_404_NOT_FOUND),
        "<path:id>:範囲外(-1)": (
            -1,
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<path:id>:型不正": (
            "ABC",
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<path:id>:None": (None, HTTP_422_UNPROCESSABLE_ENTITY),
    }

    @pytest.mark.parametrize(
        "param", list(invalid_params.values()), ids=list(invalid_params.keys())
    )
    async def test_ng_case(
        self,
        app: FastAPI,
        client: AsyncClient,
        param: tuple[any, int],
    ) -> None:
        res = await client.get(app.url_path_for("tasks:get", id=param[0]))
        assert res.status_code == param[1]


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


@pytest.mark.skipif(not is_regression, reason="not regression phase")
class TestQuery:

    # 正常ケースパラメータ
    valid_params = {
        "パラメータ無し": ({}, "{}", 20, 10, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
        "<query:limit>:(100)": (
            {"limit": 100},
            "{}",
            20,
            20,
            [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
        ),
        "<query:limit>:(3)": (
            {"limit": 3},
            "{}",
            20,
            3,
            [1, 2, 3],
        ),
        "<query:offset>:(5)": (
            {"offset": 5},
            "{}",
            20,
            10,
            [6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
        ),
        "<query:offset>:(30)": (
            {"offset": 30},
            "{}",
            20,
            0,
            [],
        ),
        "<query:sort>:(-id)": (
            {"sort": "-id"},
            "{}",
            20,
            10,
            [20, 19, 18, 17, 16, 15, 14, 13, 12, 11],
        ),
        "<query:sort>:(+deadline)": (
            {"sort": "+deadline"},
            "{}",
            20,
            10,
            [1, 2, 5, 10, 14, 3, 4, 18, 7, 11],
        ),
        "<body:title_cn>:(掃除)": (
            {},
            '{"title_cn": "掃除"}',
            3,
            3,
            [5, 7, 18],
        ),
        "<body:description_cn>:(買ってくる)": (
            {},
            '{"description_cn": "買ってくる"}',
            2,
            2,
            [6, 15],
        ),
        "<body:asaignee_id_in>:(T-002,T-001)": (
            {},
            '{"asaignee_id_in": ["T-002","T-001"]}',
            8,
            8,
            [8, 9, 10, 11, 12, 16, 18, 19],
        ),
        "<body:asaignee_id_ex>:(true)": (
            {},
            '{"asaignee_id_ex": true}',
            16,
            10,
            [1, 2, 3, 4, 5, 6, 8, 9, 10, 11],
        ),
        "<body:asaignee_id_ex>:(false)": (
            {},
            '{"asaignee_id_ex": false}',
            4,
            4,
            [7, 15, 17, 20],
        ),
        "<body:status_in>:(DOING,DONE)": (
            {},
            '{"status_in": ["DOING","DONE"]}',
            8,
            8,
            [2, 3, 6, 8, 10, 11, 12, 18],
        ),
        "<body:is_significant_eq>:(true)": (
            {},
            '{"is_significant_eq": true}',
            5,
            5,
            [1, 2, 12, 13, 15],
        ),
        "<body:deadline_from>:(2022-12-20)": (
            {},
            '{"deadline_from": "2022-12-20"}',
            3,
            3,
            [12, 15, 20],
        ),
        "<body:deadline_to>:(2022-12-02)": (
            {},
            '{"deadline_to": "2022-12-02"}',
            8,
            8,
            [1, 2, 3, 4, 5, 10, 14, 18],
        ),
        "<body:deadline>:(2022-12-04/2022-12-20)": (
            {},
            '{"deadline_from": "2022-12-04","deadline_to": "2022-12-20"}',
            4,
            4,
            [6, 9, 15, 17],
        ),
        "複合ケース": (
            {"sort": "-status,+deadline"},
            '{"status_in": ["DOING","DONE"]}',
            8,
            8,
            [11, 6, 12, 2, 10, 3, 18, 8],
        ),
    }

    @pytest.mark.parametrize(
        "param", list(valid_params.values()), ids=list(valid_params.keys())
    )
    async def test_ok_case(
        self,
        app: FastAPI,
        client: AsyncClient,
        import_task: DataFrame,
        param: tuple[any, str, int, int, List[int]],
    ) -> None:

        res = await client.post(
            app.url_path_for("tasks:query"), params=param[0], data=param[1]
        )
        assert res.status_code == HTTP_200_OK
        result = TaskPublicList(**res.json())
        # 取得件数
        assert result.count == param[2]
        assert len(result.tasks) == param[3]
        ids = [task.id for task in result.tasks]
        assert ids == param[4]

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    # 異常ケースパラメータ
    invalid_params = {
        "<query:limit>:範囲外(2000)": (
            {"limit": 2000},
            "{}",
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<query:limit>:範囲外(-1)": (
            {"limit": -1},
            "{}",
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<query:limit>:型不正": (
            {"limit": "AAA"},
            "{}",
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<query:limit>:None": (
            {"limit": None},
            "{}",
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<query:offset>:範囲外(-1)": (
            {"offset": -1},
            "{}",
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<query:offset>:型不正": (
            {"offset": "AAA"},
            "{}",
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<query:offset>:None": (
            {"offset": None},
            "{}",
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<query:sort>:フォーマット不正(符号なし)": (
            {"sort": "id"},
            "{}",
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<query:sort>:フォーマット不正(カンマなし)": (
            {"sort": "+id-status"},
            "{}",
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<query:sort>:項目不正(存在しないカラム)": (
            {"sort": "+name"},
            "{}",
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:title_cn>:文字列長超過": (
            {},
            '{"title_cn":"AAAAAAAAAABBBBBBBBBBCCCCCCCCCDDDDDDDDD"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:asaignee_id_in>:要素数不足": (
            {},
            '{"asaignee_id_in": []}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:asaignee_id_in>:要素数超過": (
            {},
            '{"asaignee_id_in": ["T-001","T-002","T-003","T-004"]}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:asaignee_id_in>:項目長不足": (
            {},
            '{"asaignee_id_in": ["10","T-002"]}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:asaignee_id_in>:項目長超過": (
            {},
            '{"asaignee_id_in": ["100000","T-002"]}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:asaignee_id_in>:型不正": (
            {},
            '{"asaignee_id_in": 200}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:asaignee_id_ex>:型不正": (
            {},
            '{"asaignee_id_ex": "AAA"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:asaignee_id>:同時指定不正([IN][EXIST])": (
            {},
            '{"asaignee_id_in": ["T-001","T-002"],"asaignee_id_ex": true}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:status_in>:要素数不足": (
            {},
            '{"status_in": []}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:status_in>:型不正": (
            {},
            '{"status_in": "AAA"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:status_in>:型不正(要素)": (
            {},
            '{"status_in": ["DOING","AAA"]}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:is_significant_eq>:型不正": (
            {},
            '{"is_significant_eq": 200}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:deadline_from>:型不正": (
            {},
            '{"deadline_from": "AAA"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:deadline_to>:型不正": (
            {},
            '{"deadline_to": "AAA"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:deadline>:順序不正": (
            {},
            '{"deadline_from": "2022-11-01","deadline_to": "2021-11-01"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body>:未定義フィールド": (
            {},
            '{"dummy":"dummy"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body>:None": (
            {},
            None,
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
    }

    @pytest.mark.parametrize(
        "param", list(invalid_params.values()), ids=list(invalid_params.keys())
    )
    async def test_ng_case(
        self,
        app: FastAPI,
        client: AsyncClient,
        param: tuple[any, str, int],
    ) -> None:
        res = await client.post(
            app.url_path_for("tasks:query"), params=param[0], data=param[1]
        )
        assert res.status_code == param[2]


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


@pytest.mark.skipif(not is_regression, reason="not regression phase")
class TestPatch:

    # 正常ケースパラメータ
    valid_params = {
        "<body:description>": TaskUpdate(description="test_description"),
        "<body:description>:null": TaskUpdate(description=None),
        "<body:asaignee_id>": TaskUpdate(asaignee_id="T-005"),
        "<body:asaignee_id>:null": TaskUpdate(asaignee_id=None),
        "<body:status>": TaskUpdate(status=TaskStatus.done),
        "<body:deadline>": TaskUpdate(deadline=date(2023, 12, 31)),
        "<body:deadline>:null": TaskUpdate(deadline=None),
        "複合ケース": TaskUpdate(
            asaignee_id="T-003", status=TaskStatus.doing, deadline=date(2023, 8, 20)
        ),
    }

    @pytest.mark.parametrize(
        "update_params", list(valid_params.values()), ids=list(valid_params.keys())
    )
    async def test_ok_case(
        self,
        app: FastAPI,
        client: AsyncClient,
        task_for_update: TaskInDB,
        update_params: TaskUpdate,
    ) -> None:
        res = await client.patch(
            app.url_path_for("tasks:patch", id=task_for_update.id),
            data=update_params.json(exclude_unset=True),
        )
        assert res.status_code == HTTP_200_OK
        updated_task = TaskInDB(**res.json())

        update_dict = update_params.dict(exclude_unset=True)
        expected = task_for_update.copy(update=update_dict)
        assert updated_task == expected

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    # 異常ケースパラメータ
    invalid_params = {
        "<path:id>:存在しない": (500, "{}", HTTP_404_NOT_FOUND),
        "<path:id>:範囲外(-1)": (
            -1,
            "{}",
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<path:id>:型不正": (
            "ABC",
            "{}",
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<path:id>:None": (None, "{}", HTTP_422_UNPROCESSABLE_ENTITY),
        "<body:asaignee_id>:桁数不足": (
            1,
            '{"asaignee_id":"10"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:asaignee_id>:桁数超過": (
            1,
            '{"asaignee_id":"000000"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:status>:区分値外": (
            1,
            '{"status":"NO_TYPE"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:status>:None": (
            1,
            '{"status":None}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:deadline>:型不正": (
            1,
            '{"deadline":10}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:deadline>:過去日付": (
            1,
            '{"deadline": "2000-12-31"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body>:変更不可フィールド(title)": (
            1,
            '{"title":"dummy"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body>:変更不可フィールド(is_significant)": (
            1,
            '{"is_significant":true}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body>:None": (
            1,
            None,
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
    }

    @pytest.mark.parametrize(
        "param", list(invalid_params.values()), ids=list(invalid_params.keys())
    )
    async def test_ng_case(
        self,
        app: FastAPI,
        client: AsyncClient,
        param: tuple[any, str, int],
    ) -> None:
        res = await client.patch(
            app.url_path_for("tasks:patch", id=param[0]),
            data=param[1],
        )
        assert res.status_code == param[2]


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


@pytest.mark.skipif(not is_regression, reason="not regression phase")
class TestDelete:
    async def test_ok_case(
        self, app: FastAPI, client: AsyncClient, task_for_delete: TaskInDB
    ) -> None:

        res = await client.delete(
            app.url_path_for("tasks:delete", id=task_for_delete.id)
        )
        assert res.status_code == HTTP_200_OK
        get_task = TaskInDB(**res.json())
        assert get_task == task_for_delete

        # 再検索して存在しないこと
        res = await client.get(app.url_path_for("tasks:get", id=task_for_delete.id))
        assert res.status_code == HTTP_404_NOT_FOUND

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    # 異常ケースパラメータ
    invalid_params = {
        "<path:id>:存在しない": (500, HTTP_404_NOT_FOUND),
        "<path:id>:範囲外(-1)": (
            -1,
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<path:id>:型不正": (
            "ABC",
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<path:id>:None": (None, HTTP_422_UNPROCESSABLE_ENTITY),
    }

    @pytest.mark.parametrize(
        "param", list(invalid_params.values()), ids=list(invalid_params.keys())
    )
    async def test_ng_case(
        self,
        app: FastAPI,
        client: AsyncClient,
        param: tuple[any, int],
    ) -> None:
        res = await client.delete(app.url_path_for("tasks:delete", id=param[0]))
        assert res.status_code == param[1]

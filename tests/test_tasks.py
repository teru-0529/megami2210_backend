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
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from app.api.schemas.accounts import ProfileInDB
from app.api.schemas.tasks import (
    TaskCreate,
    TaskInDB,
    TaskPublicList,
    TaskUpdate,
    TaskWithAccount,
)
from app.models.segment_values import TaskStatus
from app.services import auth_service
from app.services.accounts import AccountService
from app.services.tasks import TaskService

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def fixed_task(session: AsyncSession, general_account: ProfileInDB) -> TaskInDB:
    new_task = TaskCreate(
        title="fixed task",
        description="fixed task",
        asaignee_id="T-903",
        deadline=date(2030, 12, 31),
    )
    token = auth_service.create_token_for_user(account=general_account)
    service = TaskService()
    created_task = await service.create(session=session, token=token, new_task=new_task)
    yield created_task
    await service.delete(session=session, id=created_task.id)


@pytest_asyncio.fixture
async def fixed_task_with_account(
    session: AsyncSession, fixed_task: TaskInDB
) -> TaskWithAccount:
    service = AccountService()
    registrant = await service.get_by_id(session=session, id=fixed_task.registrant_id)
    asaignee = await service.get_by_id(session=session, id=fixed_task.asaignee_id)
    task_with_account = TaskWithAccount(
        id=fixed_task.id,
        registrant=registrant,
        title=fixed_task.title,
        description=fixed_task.description,
        asaignee=asaignee,
        status=fixed_task.status,
        is_significant=fixed_task.is_significant,
        deadline=fixed_task.deadline,
    )
    yield task_with_account


@pytest_asyncio.fixture
async def task_for_update(
    session: AsyncSession, general_account: ProfileInDB
) -> TaskInDB:
    new_task = TaskCreate(
        title="updated task",
        description="updated task",
        asaignee_id="T-903",
        deadline=date(2030, 12, 31),
    )
    token = auth_service.create_token_for_user(account=general_account)
    service = TaskService()
    created_task = await service.create(session=session, token=token, new_task=new_task)
    yield created_task
    await service.delete(session=session, id=created_task.id)


@pytest_asyncio.fixture
async def task_for_delete(
    session: AsyncSession, general_account: ProfileInDB
) -> TaskInDB:
    new_task = TaskCreate(
        title="updated task",
        description="updated task",
        asaignee_id="T-903",
        deadline=date(2030, 12, 31),
    )
    token = auth_service.create_token_for_user(account=general_account)
    service = TaskService()
    created_task = await service.create(session=session, token=token, new_task=new_task)
    return created_task


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


@pytest.fixture
def import_task(s_engine: Engine) -> DataFrame:
    datas: DataFrame = read_csv(
        "tests/data/test_task_data.csv", encoding="utf-8", dtype={4: str}
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


class TestRouteExists:
    async def test_create(self, app: FastAPI, client: AsyncClient) -> None:
        try:
            await client.post(app.url_path_for("tasks:create"), json={})
        except NoMatchFound:
            pytest.fail("route not exist")

    async def test_get(self, app: FastAPI, client: AsyncClient) -> None:
        try:
            await client.get(app.url_path_for("tasks:get", id=1))
        except NoMatchFound:
            pytest.fail("route not exist")

    async def test_query(self, app: FastAPI, client: AsyncClient) -> None:
        try:
            await client.get(app.url_path_for("tasks:search"))
        except NoMatchFound:
            pytest.fail("route not exist")

    async def test_patch(self, app: FastAPI, client: AsyncClient) -> None:
        try:
            await client.get(app.url_path_for("tasks:patch", id=1))
        except NoMatchFound:
            pytest.fail("route not exist")

    async def test_delete(self, app: FastAPI, client: AsyncClient) -> None:
        try:
            await client.get(app.url_path_for("tasks:delete", id=1))
        except NoMatchFound:
            pytest.fail("route not exist")


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class TestCreate:

    # ??????????????????????????????
    valid_params = {
        "<body:full>": TaskCreate(
            title="test task",
            description="test description",
            asaignee_id="T-901",
            is_significant=True,
            deadline=date(2050, 12, 31),
        ),
        "<body:asaignee_id>:????????????": TaskCreate(
            title="test task",
            description="??????????????????",
            is_significant=True,
            deadline=date(2050, 12, 31),
        ),
        "<body:is_significant>??????????????????": TaskCreate(
            title="test task",
            description="test description",
            asaignee_id="T-901",
            deadline=date(2050, 12, 31),
        ),
        "<body:deadline>:????????????": TaskCreate(
            title="test task",
            description="test description",
            asaignee_id="T-901",
            is_significant=False,
        ),
    }

    @pytest.mark.parametrize(
        "new_task", list(valid_params.values()), ids=list(valid_params.keys())
    )
    # ???????????????
    @pytest.mark.ok
    async def test_ok(
        self, app: FastAPI, general_client: AsyncClient, new_task: TaskCreate
    ) -> None:

        res = await general_client.post(
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

    # ?????????????????????????????????????????????????????????
    @pytest.mark.ng
    async def test_ng_activation(
        self, app: FastAPI, non_active_client: AsyncClient
    ) -> None:
        res = await non_active_client.post(
            app.url_path_for("tasks:create"),
            data='{"title":"dummy"}',
        )
        assert res.status_code == HTTP_401_UNAUTHORIZED

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    # ????????????????????????????????????
    @pytest.mark.ng
    async def test_ng_permission(
        self, app: FastAPI, provisional_client: AsyncClient
    ) -> None:
        res = await provisional_client.post(
            app.url_path_for("tasks:create"),
            data='{"title":"dummy"}',
        )
        assert res.status_code == HTTP_403_FORBIDDEN

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    # ??????????????????????????????
    invalid_params = {
        "<body:None>": ("{}", HTTP_422_UNPROCESSABLE_ENTITY),
        "<body:title>:??????": ('{"description":"dummy"}', HTTP_422_UNPROCESSABLE_ENTITY),
        "<body:title>:????????????": (
            '{"title":"000000000100000000010000000001000000001"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:asaignee_id>:????????????": (
            '{"title":"dummy","asaignee_id":"10"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:asaignee_id>:????????????": (
            '{"title":"dummy","asaignee_id":"000000"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:is_significant>:?????????": (
            '{"title":"dummy","is_significant":10}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:deadline>:?????????": (
            '{"title":"dummy","deadline":10}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:deadline>:????????????": (
            '{"title":"dummy","deadline": "2000-12-31"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body>:????????????????????????": (
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
    # ???????????????????????????????????????????????????
    @pytest.mark.ng
    async def test_ng_validation(
        self,
        app: FastAPI,
        general_client: AsyncClient,
        param: tuple[str, int],
    ) -> None:
        res = await general_client.post(
            app.url_path_for("tasks:create"),
            data=param[0],
        )
        assert res.status_code == param[1]

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    # ??????????????????????????????????????????
    @pytest.mark.ng
    async def test_ng_foreignkey(
        self, app: FastAPI, general_client: AsyncClient
    ) -> None:
        new_task = TaskCreate(
            title="test task",
            asaignee_id="T-501",
        )
        res = await general_client.post(
            app.url_path_for("tasks:create"),
            data=new_task.json(exclude_unset=True),
        )
        assert res.status_code == HTTP_400_BAD_REQUEST


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class TestGet:

    # ???????????????
    @pytest.mark.ok
    async def test_ok(
        self, app: FastAPI, provisional_client: AsyncClient, fixed_task: TaskInDB
    ) -> None:

        res = await provisional_client.get(
            app.url_path_for("tasks:get", id=fixed_task.id)
        )
        assert res.status_code == HTTP_200_OK
        get_task = TaskInDB(**res.json())
        assert get_task == fixed_task

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    # ???????????????(????????????????????????????????????)
    @pytest.mark.ok
    async def test_ok_with_account(
        self,
        app: FastAPI,
        provisional_client: AsyncClient,
        fixed_task_with_account: TaskWithAccount,
    ) -> None:

        res = await provisional_client.get(
            app.url_path_for("tasks:get", id=fixed_task_with_account.id),
            params={"sub-resources": "account"},
        )
        assert res.status_code == HTTP_200_OK
        get_task = TaskWithAccount(**res.json())
        assert get_task == fixed_task_with_account

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    # ?????????????????????????????????????????????????????????
    @pytest.mark.ng
    async def test_ng_activation(
        self, app: FastAPI, non_active_client: AsyncClient
    ) -> None:
        res = await non_active_client.get(app.url_path_for("tasks:get", id=1))
        assert res.status_code == HTTP_401_UNAUTHORIZED

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    # ??????????????????????????????
    invalid_params = {
        "<path:id>:???????????????": (500, HTTP_404_NOT_FOUND),
        "<path:id>:?????????(-1)": (
            -1,
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<path:id>:?????????": (
            "ABC",
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<path:id>:None": (None, HTTP_422_UNPROCESSABLE_ENTITY),
    }

    @pytest.mark.parametrize(
        "param", list(invalid_params.values()), ids=list(invalid_params.keys())
    )
    # ???????????????????????????????????????????????????
    @pytest.mark.ng
    async def test_ng_validation(
        self,
        app: FastAPI,
        provisional_client: AsyncClient,
        param: tuple[any, int],
    ) -> None:
        res = await provisional_client.get(app.url_path_for("tasks:get", id=param[0]))
        assert res.status_code == param[1]


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class TestSearch:

    # ??????????????????????????????
    valid_params = {
        "?????????????????????": ({}, "{}", 20, 10, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
        "??????????????????(???????????????)": (
            {"sub-resources": "account"},
            "{}",
            20,
            10,
            [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        ),
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
        "<body:title_cn>:(??????)": (
            {},
            '{"title_cn": "??????"}',
            3,
            3,
            [5, 7, 18],
        ),
        "<body:description_cn>:(???????????????)": (
            {},
            '{"description_cn": "???????????????"}',
            2,
            2,
            [6, 15],
        ),
        "<body:asaignee_id_in>:(T-902,T-901)": (
            {},
            '{"asaignee_id_in": ["T-902","T-901"]}',
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
        "???????????????": (
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
    # ???????????????
    @pytest.mark.ok
    async def test_ok(
        self,
        app: FastAPI,
        provisional_client: AsyncClient,
        import_task: DataFrame,
        param: tuple[any, str, int, int, List[int]],
    ) -> None:

        res = await provisional_client.post(
            app.url_path_for("tasks:search"), params=param[0], data=param[1]
        )
        assert res.status_code == HTTP_200_OK
        result = TaskPublicList(**res.json())
        # ????????????
        assert result.count == param[2]
        assert len(result.tasks) == param[3]
        ids = [task.id for task in result.tasks]
        assert ids == param[4]

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    # ?????????????????????????????????????????????????????????
    @pytest.mark.ng
    async def test_ng_activation(
        self, app: FastAPI, non_active_client: AsyncClient
    ) -> None:
        res = await non_active_client.post(
            app.url_path_for("tasks:search"), params={}, data="{}"
        )
        assert res.status_code == HTTP_401_UNAUTHORIZED

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    # ??????????????????????????????
    invalid_params = {
        "<query:limit>:?????????(2000)": (
            {"limit": 2000},
            "{}",
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<query:limit>:?????????(-1)": (
            {"limit": -1},
            "{}",
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<query:limit>:?????????": (
            {"limit": "AAA"},
            "{}",
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<query:limit>:None": (
            {"limit": None},
            "{}",
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<query:offset>:?????????(-1)": (
            {"offset": -1},
            "{}",
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<query:offset>:?????????": (
            {"offset": "AAA"},
            "{}",
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<query:offset>:None": (
            {"offset": None},
            "{}",
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<query:sort>:????????????????????????(????????????)": (
            {"sort": "id"},
            "{}",
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<query:sort>:????????????????????????(???????????????)": (
            {"sort": "+id-status"},
            "{}",
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<query:sort>:????????????(????????????????????????)": (
            {"sort": "+name"},
            "{}",
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:title_cn>:??????????????????": (
            {},
            '{"title_cn":"AAAAAAAAAABBBBBBBBBBCCCCCCCCCDDDDDDDDD"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:asaignee_id_in>:???????????????": (
            {},
            '{"asaignee_id_in": []}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:asaignee_id_in>:???????????????": (
            {},
            '{"asaignee_id_in": ["T-901","T-902","T-903","T-904"]}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:asaignee_id_in>:???????????????": (
            {},
            '{"asaignee_id_in": ["10","T-902"]}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:asaignee_id_in>:???????????????": (
            {},
            '{"asaignee_id_in": ["100000","T-902"]}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:asaignee_id_in>:?????????": (
            {},
            '{"asaignee_id_in": 200}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:asaignee_id_ex>:?????????": (
            {},
            '{"asaignee_id_ex": "AAA"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:asaignee_id>:??????????????????([IN][EXIST])": (
            {},
            '{"asaignee_id_in": ["T-901","T-902"],"asaignee_id_ex": true}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:status_in>:???????????????": (
            {},
            '{"status_in": []}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:status_in>:?????????": (
            {},
            '{"status_in": "AAA"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:status_in>:?????????(??????)": (
            {},
            '{"status_in": ["DOING","AAA"]}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:is_significant_eq>:?????????": (
            {},
            '{"is_significant_eq": 200}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:deadline_from>:?????????": (
            {},
            '{"deadline_from": "AAA"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:deadline_to>:?????????": (
            {},
            '{"deadline_to": "AAA"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:deadline>:????????????": (
            {},
            '{"deadline_from": "2022-11-01","deadline_to": "2021-11-01"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body>:????????????????????????": (
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
    # ???????????????????????????????????????????????????
    @pytest.mark.ng
    async def test_ng_validation(
        self,
        app: FastAPI,
        provisional_client: AsyncClient,
        param: tuple[any, str, int],
    ) -> None:
        res = await provisional_client.post(
            app.url_path_for("tasks:search"), params=param[0], data=param[1]
        )
        assert res.status_code == param[2]


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class TestPatch:

    # ??????????????????????????????
    valid_params = {
        "<body:description>": TaskUpdate(description="test_description"),
        "<body:description>:null": TaskUpdate(description=None),
        "<body:asaignee_id>": TaskUpdate(asaignee_id="T-901"),
        "<body:asaignee_id>:null": TaskUpdate(asaignee_id=None),
        "<body:status>": TaskUpdate(status=TaskStatus.done),
        "<body:deadline>": TaskUpdate(deadline=date(2023, 12, 31)),
        "<body:deadline>:null": TaskUpdate(deadline=None),
        "???????????????": TaskUpdate(
            asaignee_id="T-902", status=TaskStatus.doing, deadline=date(2023, 8, 20)
        ),
    }

    @pytest.mark.parametrize(
        "update_params", list(valid_params.values()), ids=list(valid_params.keys())
    )
    # ???????????????
    @pytest.mark.ok
    async def test_ok(
        self,
        app: FastAPI,
        general_client: AsyncClient,
        task_for_update: TaskInDB,
        update_params: TaskUpdate,
    ) -> None:
        res = await general_client.patch(
            app.url_path_for("tasks:patch", id=task_for_update.id),
            data=update_params.json(exclude_unset=True),
        )
        assert res.status_code == HTTP_200_OK
        updated_task = TaskInDB(**res.json())

        update_dict = update_params.dict(exclude_unset=True)
        expected = task_for_update.copy(update=update_dict)
        assert updated_task == expected

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    # ?????????????????????????????????????????????????????????
    @pytest.mark.ng
    async def test_ng_activation(
        self, app: FastAPI, non_active_client: AsyncClient
    ) -> None:
        res = await non_active_client.patch(
            app.url_path_for("tasks:patch", id=1),
            data='{"description":"dummy"}',
        )
        assert res.status_code == HTTP_401_UNAUTHORIZED

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    # ????????????????????????????????????
    @pytest.mark.ng
    async def test_ng_permission(
        self, app: FastAPI, provisional_client: AsyncClient
    ) -> None:
        res = await provisional_client.patch(
            app.url_path_for("tasks:patch", id=1),
            data='{"description":"dummy"}',
        )
        assert res.status_code == HTTP_403_FORBIDDEN

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    # ??????????????????????????????
    invalid_params = {
        "<path:id>:???????????????": (500, "{}", HTTP_404_NOT_FOUND),
        "<path:id>:?????????(-1)": (
            -1,
            "{}",
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<path:id>:?????????": (
            "ABC",
            "{}",
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<path:id>:None": (None, "{}", HTTP_422_UNPROCESSABLE_ENTITY),
        "<body:asaignee_id>:????????????": (
            1,
            '{"asaignee_id":"10"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:asaignee_id>:????????????": (
            1,
            '{"asaignee_id":"000000"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:status>:????????????": (
            1,
            '{"status":"NO_TYPE"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:status>:None": (
            1,
            '{"status":None}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:deadline>:?????????": (
            1,
            '{"deadline":10}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body:deadline>:????????????": (
            1,
            '{"deadline": "2000-12-31"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body>:???????????????????????????(title)": (
            1,
            '{"title":"dummy"}',
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<body>:???????????????????????????(is_significant)": (
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
    # ???????????????????????????????????????????????????
    @pytest.mark.ng
    async def test_ng_validation(
        self,
        app: FastAPI,
        general_client: AsyncClient,
        param: tuple[any, str, int],
    ) -> None:
        res = await general_client.patch(
            app.url_path_for("tasks:patch", id=param[0]),
            data=param[1],
        )
        assert res.status_code == param[2]

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    # ??????????????????????????????????????????
    @pytest.mark.ng
    async def test_ng_foreignkey(
        self, app: FastAPI, general_client: AsyncClient, task_for_update: TaskInDB
    ) -> None:
        res = await general_client.patch(
            app.url_path_for("tasks:patch", id=task_for_update.id),
            data='{"asaignee_id":"T-501"}',
        )
        assert res.status_code == HTTP_400_BAD_REQUEST


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class TestDelete:

    # ???????????????
    @pytest.mark.ok
    async def test_ok(
        self, app: FastAPI, general_client: AsyncClient, task_for_delete: TaskInDB
    ) -> None:

        res = await general_client.delete(
            app.url_path_for("tasks:delete", id=task_for_delete.id)
        )
        assert res.status_code == HTTP_200_OK
        get_task = TaskInDB(**res.json())
        assert get_task == task_for_delete

        # ????????????????????????????????????
        res = await general_client.get(
            app.url_path_for("tasks:get", id=task_for_delete.id)
        )
        assert res.status_code == HTTP_404_NOT_FOUND

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    # ?????????????????????????????????????????????????????????
    @pytest.mark.ng
    async def test_ng_activation(
        self, app: FastAPI, non_active_client: AsyncClient
    ) -> None:
        res = await non_active_client.delete(app.url_path_for("tasks:delete", id=1))
        assert res.status_code == HTTP_401_UNAUTHORIZED

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    # ????????????????????????????????????
    @pytest.mark.ng
    async def test_ng_permission(
        self, app: FastAPI, provisional_client: AsyncClient
    ) -> None:
        res = await provisional_client.delete(app.url_path_for("tasks:delete", id=1))
        assert res.status_code == HTTP_403_FORBIDDEN

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    # ??????????????????????????????
    invalid_params = {
        "<path:id>:???????????????": (500, HTTP_404_NOT_FOUND),
        "<path:id>:?????????(-1)": (
            -1,
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<path:id>:?????????": (
            "ABC",
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        "<path:id>:None": (None, HTTP_422_UNPROCESSABLE_ENTITY),
    }

    @pytest.mark.parametrize(
        "param", list(invalid_params.values()), ids=list(invalid_params.keys())
    )
    # ???????????????????????????????????????????????????
    @pytest.mark.ng
    async def test_ng_validation(
        self,
        app: FastAPI,
        general_client: AsyncClient,
        param: tuple[any, int],
    ) -> None:
        res = await general_client.delete(app.url_path_for("tasks:delete", id=param[0]))
        assert res.status_code == param[1]

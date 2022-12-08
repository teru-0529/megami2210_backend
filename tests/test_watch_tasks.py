#!/usr/bin/python3
# test_watch_tasks.py

from typing import List

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from starlette.routing import NoMatchFound
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from app.api.schemas.tasks import (
    TaskCreate,
    TaskInDB,
    TaskPublicList,
    TaskWithWatchNote,
)

pytestmark = pytest.mark.asyncio


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class TestRouteExists:
    async def test_put_watch_task(self, app: FastAPI, client: AsyncClient) -> None:
        try:
            await client.put(app.url_path_for("mine:put-watch-task", id=1))
        except NoMatchFound:
            pytest.fail("route not exist")

    async def test_delete_watch_task(self, app: FastAPI, client: AsyncClient) -> None:
        try:
            await client.delete(app.url_path_for("mine:delete-watch-task", id=1))
        except NoMatchFound:
            pytest.fail("route not exist")

    async def test_get_watch_tasks(self, app: FastAPI, client: AsyncClient) -> None:
        try:
            await client.get(app.url_path_for("mine:get-watch-tasks"))
        except NoMatchFound:
            pytest.fail("route not exist")


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class TestPut:

    # 異常ケース（認証エラー）
    @pytest.mark.ng
    async def test_ng_authentication(self, app: FastAPI, client: AsyncClient) -> None:
        res = await client.put(app.url_path_for("mine:put-watch-task", id=1))
        assert res.status_code == HTTP_401_UNAUTHORIZED

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    # 異常ケース（アクティベーションエラー）
    @pytest.mark.ng
    async def test_ng_activation(
        self, app: FastAPI, non_active_client: AsyncClient
    ) -> None:
        res = await non_active_client.put(
            app.url_path_for("mine:put-watch-task", id=1), data="{}"
        )
        assert res.status_code == HTTP_401_UNAUTHORIZED

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
        "<body>:None": (
            1,
            None,
            HTTP_422_UNPROCESSABLE_ENTITY,
        ),
    }

    @pytest.mark.parametrize(
        "param", list(invalid_params.values()), ids=list(invalid_params.keys())
    )
    # 異常ケース（バリデーションエラー）
    @pytest.mark.ng
    async def test_ng_validation(
        self,
        app: FastAPI,
        general_client: AsyncClient,
        param: tuple[str, int],
    ) -> None:
        res = await general_client.put(
            app.url_path_for("mine:put-watch-task", id=param[0]), data=param[1]
        )
        assert res.status_code == param[2]


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class TestDelete:

    # 異常ケース（認証エラー）
    @pytest.mark.ng
    async def test_ng_authentication(self, app: FastAPI, client: AsyncClient) -> None:
        res = await client.delete(app.url_path_for("mine:delete-watch-task", id=1))
        assert res.status_code == HTTP_401_UNAUTHORIZED

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    # 異常ケース（アクティベーションエラー）
    @pytest.mark.ng
    async def test_ng_activation(
        self, app: FastAPI, non_active_client: AsyncClient
    ) -> None:
        res = await non_active_client.delete(
            app.url_path_for("mine:delete-watch-task", id=1)
        )
        assert res.status_code == HTTP_401_UNAUTHORIZED

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
    # 異常ケース（バリデーションエラー）
    @pytest.mark.ng
    async def test_ng_validation(
        self,
        app: FastAPI,
        general_client: AsyncClient,
        param: tuple[str, int],
    ) -> None:
        res = await general_client.delete(
            app.url_path_for("mine:delete-watch-task", id=param[0])
        )
        assert res.status_code == param[1]


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class TestGet:

    # 異常ケース（認証エラー）
    @pytest.mark.ng
    async def test_ng_authentication(self, app: FastAPI, client: AsyncClient) -> None:
        res = await client.get(app.url_path_for("mine:get-watch-tasks"))
        assert res.status_code == HTTP_401_UNAUTHORIZED

    # ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----

    # 異常ケース（アクティベーションエラー）
    @pytest.mark.ng
    async def test_ng_activation(
        self, app: FastAPI, non_active_client: AsyncClient
    ) -> None:
        res = await non_active_client.get(app.url_path_for("mine:get-watch-tasks"))
        assert res.status_code == HTTP_401_UNAUTHORIZED


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class TestUsecase:

    # 正常ケース
    @pytest.mark.ok
    async def test_ok(
        self,
        app: FastAPI,
        general_client: AsyncClient,
    ) -> None:

        # タスク登録（3件）
        res = await general_client.post(
            app.url_path_for("tasks:create"),
            data=TaskCreate(title="task1").json(exclude_unset=True),
        )
        assert res.status_code == HTTP_201_CREATED
        task1 = TaskInDB(**res.json())

        res = await general_client.post(
            app.url_path_for("tasks:create"),
            data=TaskCreate(title="task2").json(exclude_unset=True),
        )
        assert res.status_code == HTTP_201_CREATED
        task2 = TaskInDB(**res.json())

        res = await general_client.post(
            app.url_path_for("tasks:create"),
            data=TaskCreate(title="task3").json(exclude_unset=True),
        )
        assert res.status_code == HTTP_201_CREATED
        task3 = TaskInDB(**res.json())

        # タスク検索（3件）
        res = await general_client.post(
            app.url_path_for("tasks:search"), params={}, data="{}"
        )
        assert res.status_code == HTTP_200_OK
        result = TaskPublicList(**res.json())
        assert result.count == 3

        # 監視タスク取得（0件）
        res = await general_client.get(app.url_path_for("mine:get-watch-tasks"))
        assert res.status_code == HTTP_200_OK
        watch_list: List[TaskWithWatchNote] = res.json()
        assert watch_list == []

        # 監視タスク登録（task1）
        res = await general_client.put(
            app.url_path_for("mine:put-watch-task", id=task1.id), data='{"note":"note"}'
        )
        assert res.status_code == HTTP_200_OK

        # 監視タスク取得（1件）
        res = await general_client.get(app.url_path_for("mine:get-watch-tasks"))
        assert res.status_code == HTTP_200_OK
        watch_list: List[TaskWithWatchNote] = res.json()
        assert len(watch_list) == 1
        assert watch_list[0]["id"] == task1.id
        assert watch_list[0]["note"] == "note"

        # 監視タスク更新（task1）
        res = await general_client.put(
            app.url_path_for("mine:put-watch-task", id=task1.id),
            data='{"note":"new_note"}',
        )
        assert res.status_code == HTTP_200_OK

        # 監視タスク取得（1件）
        res = await general_client.get(app.url_path_for("mine:get-watch-tasks"))
        assert res.status_code == HTTP_200_OK
        watch_list: List[TaskWithWatchNote] = res.json()
        assert len(watch_list) == 1
        assert watch_list[0]["id"] == task1.id
        assert watch_list[0]["note"] == "new_note"

        # 監視タスク登録（task2）
        res = await general_client.put(
            app.url_path_for("mine:put-watch-task", id=task2.id), data='{"note":"note"}'
        )
        assert res.status_code == HTTP_200_OK

        # 監視タスク取得（2件）
        res = await general_client.get(app.url_path_for("mine:get-watch-tasks"))
        assert res.status_code == HTTP_200_OK
        watch_list: List[TaskWithWatchNote] = res.json()
        assert len(watch_list) == 2

        # 監視タスク削除（task3）
        res = await general_client.delete(
            app.url_path_for("mine:delete-watch-task", id=task3.id)
        )
        assert res.status_code == HTTP_200_OK

        # 監視タスク取得（2件）
        res = await general_client.get(app.url_path_for("mine:get-watch-tasks"))
        assert res.status_code == HTTP_200_OK
        watch_list: List[TaskWithWatchNote] = res.json()
        assert len(watch_list) == 2

        # 監視タスク削除（task2）
        res = await general_client.delete(
            app.url_path_for("mine:delete-watch-task", id=task2.id)
        )
        assert res.status_code == HTTP_200_OK

        # 監視タスク取得（1件）
        res = await general_client.get(app.url_path_for("mine:get-watch-tasks"))
        assert res.status_code == HTTP_200_OK
        watch_list: List[TaskWithWatchNote] = res.json()
        assert len(watch_list) == 1
        assert watch_list[0]["id"] == task1.id

        # タスク削除（task1）
        res = await general_client.delete(app.url_path_for("tasks:delete", id=task1.id))
        assert res.status_code == HTTP_200_OK

        # 監視タスク取得（0件）
        res = await general_client.get(app.url_path_for("mine:get-watch-tasks"))
        assert res.status_code == HTTP_200_OK
        watch_list: List[TaskWithWatchNote] = res.json()
        assert watch_list == []

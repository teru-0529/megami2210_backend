#!/usr/bin/python3
# test_tasks.py

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from starlette.status import HTTP_404_NOT_FOUND, HTTP_422_UNPROCESSABLE_ENTITY


class TestTasksRoutes:
    @pytest.mark.asyncio
    async def test_route_exist(self, app: FastAPI, client: AsyncClient) -> None:
        res = await client.post(app.url_path_for("tasks:create"), json={})
        assert res.status_code != HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_invalid_input_raises_error(
        self, app: FastAPI, client: AsyncClient
    ) -> None:
        res = await client.post(app.url_path_for("tasks:create"), json={})
        assert res.status_code == HTTP_422_UNPROCESSABLE_ENTITY

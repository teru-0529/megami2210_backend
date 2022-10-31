#!/usr/bin/python3
# __init__.py

from app.api.routes.tasks import router as task_router
from fastapi import APIRouter

router = APIRouter()


@router.get(
    "/health",
    name="health:check",
    responses={
        200: {
            "description": "check result",
            "content": {"application/json": {"example": {"health": "ok"}}},
        },
    },
)
async def health_check() -> dict:
    """
    APIサーバーのヘルスチェック。:

    """
    ok = {"health": "ok"}
    return ok


router.include_router(task_router, prefix="/tasks", tags=["tasks"])

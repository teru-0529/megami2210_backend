#!/usr/bin/python3
# __init__.py

from fastapi import APIRouter

from app.api.routes.tasks import router as task_router
from app.api.routes.accounts import router as account_raoute
from app.api.schemas.base import Message

router = APIRouter()


@router.get(
    "/health",
    name="health:check",
    responses={
        200: {
            "model": Message,
            "description": "state of api server",
            "content": {
                "application/json": {"example": {"detail": "APIサーバーは正常に稼働しています。"}}
            },
        },
    },
)
async def health_check() -> dict:  # pragma: no cover
    """
    APIサーバーのヘルスチェック。:

    """
    ok = {"detail": "APIサーバーは正常に稼働しています。"}
    return ok


router.include_router(task_router, prefix="/tasks", tags=["tasks"])
router.include_router(account_raoute, prefix="/accounts", tags=["accounts"])

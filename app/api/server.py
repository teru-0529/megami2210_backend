#!/usr/bin/python3
# server.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.core.config import API_PREFIX, PROJECT_NAME, VERSION


def get_application():
    app = FastAPI(title=PROJECT_NAME, version=VERSION)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=API_PREFIX)
    return app


app = get_application()

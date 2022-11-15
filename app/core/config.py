#!/usr/bin/python3
# config.py

from starlette.config import Config
from starlette.datastructures import Secret

config = Config(".env")

PROJECT_NAME = "MEGUMI2210(TODO Application)"
VERSION = "0.9.0"
API_PREFIX = "/api"

SECRET_KEY = config("SECRET_KEY", cast=Secret, default="CHANGEME")
POSTGRES_USER = config("POSTGRES_USER", cast=str)
POSTGRES_PASSWORD = config("POSTGRES_PASSWORD", cast=Secret)
POSTGRES_SERVER = config("POSTGRES_SERVER", cast=str, default="db")
POSTGRES_PORT = config("POSTGRES_PORT", cast=str, default="5432")
POSTGRES_DB = config("POSTGRES_DB", cast=str)

SYNC_DIALECT = "postgresql+psycopg2"
ASYNC_DIALECT = "postgresql+asyncpg"


def db_url(dialect: str, server: str = POSTGRES_SERVER) -> str:
    return f"{dialect}://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{server}:{POSTGRES_PORT}/{POSTGRES_DB}"


SYNC_URL = db_url(dialect=SYNC_DIALECT)
ASYNC_URL = db_url(dialect=ASYNC_DIALECT)

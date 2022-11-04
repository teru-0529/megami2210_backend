#!/usr/bin/python3
# database.py

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import DB_ASYNC_URL

async_engine = create_async_engine(DB_ASYNC_URL, echo=True)
async_session = sessionmaker(
    autocommit=False, autoflush=False, bind=async_engine, class_=AsyncSession
)


async def get_db():
    async with async_session() as session:
        yield session

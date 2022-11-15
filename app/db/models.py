#!/usr/bin/python3
# models.py

from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session

from app.core.config import SYNC_URL

sync_engine = create_engine(SYNC_URL, echo=False)
sync_session = Session(sync_engine)

Base = automap_base()
Base.prepare(sync_engine, reflect=True, schema="todo")

# Taskテーブル
Task = Base.classes.tasks


def printTaskList() -> None:  # pragma: no cover
    q = sync_session.query(Task).order_by(Task.id.desc())

    for t in q:
        print(t.id, t.title, t.status)

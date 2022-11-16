#!/usr/bin/python3
# models.py

from sqlalchemy.ext.automap import automap_base

from app.core.database import SyncCon

con = SyncCon()
engine = con.engine()

Base = automap_base()
Base.prepare(engine, reflect=True, schema="todo")

# Taskテーブル
Task = Base.classes.tasks

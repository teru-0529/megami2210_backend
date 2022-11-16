#!/usr/bin/python3
# models.py

from sqlalchemy.ext.automap import automap_base

from app.core.database import SyncCon

con = SyncCon()
s_engine = con.engine()

Base = automap_base()
Base.prepare(s_engine, reflect=True, schema="todo")

# Taskモデル
Task = Base.classes.tasks

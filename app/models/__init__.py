#!/usr/bin/python3
# __init__.py

from sqlalchemy.ext.automap import automap_base

from app.core.database import SyncCon

con = SyncCon()
s_engine = con.engine()

Base = automap_base()
Base.prepare(s_engine, reflect=True, schema="todo")

# Taskモデル
m_Task = Base.classes.tasks

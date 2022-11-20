from sqlalchemy.ext.automap import automap_base

from app.core.database import SyncCon

con = SyncCon()
s_engine = con.engine()

# todoスキーマ
BaseTD = automap_base()
BaseTD.prepare(s_engine, reflect=True, schema="todo")

# Taskモデル
td_Task = BaseTD.classes.tasks

# accountスキーマ
BaseAC = automap_base()
BaseAC.prepare(s_engine, reflect=True, schema="account")

# Profileモデル
ac_Profile = BaseAC.classes.profiles

# Authモデル
ac_Auth = BaseAC.classes.authes

# Profileモデル
ac_WatchTask = BaseAC.classes.watch_tasks

#!/usr/bin/python3
# config.py

from enum import Enum

# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class Base(str, Enum):
    pass

    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class TaskStatus(Base):
    todo = "TODO"
    doing = "DOING"
    done = "DONE"

    def description() -> str:
        return """
タスク状況:
  * `TODO` - 未対応
  * `DOING` - 対応中
  * `DONE` - 完了
    """


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class AccountTypes(Base):
    administrator = "ADMINISTRATOR"
    general = "GENERAL"
    provisional = "PROVISIONAL"

    def description() -> str:
        return """
アカウント種類:
  * `ADMINISTRATOR` - 管理ユーザー
  * `GENERAL` - 一般ユーザー
  * `PROVISIONAL` - 仮発行ユーザー
    """

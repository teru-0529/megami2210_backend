#!/usr/bin/python3
# config.py

from enum import Enum


class Base(str, Enum):
    pass

    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))


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

#!/usr/bin/python3
# __init__.py

from typing import List

from sqlalchemy import asc, desc
from sqlalchemy.sql.functions import FunctionElement


class QueryParam:
    offset: int = 0
    limit: int = 10
    sort: List[FunctionElement]
    filter: List[FunctionElement]

    def __init__(
        self, *, columns: List[str], offset: int, limit: int, sort: str
    ) -> None:
        ls = sort.split(",")
        if "+id" not in ls:
            ls.append("+id")  # デフォルトのソート条件を追加 TODO:

        ls = [(v.strip()[0], v.strip()[1:]) for v in ls]  # 符号/値、のタプルに分割

        err_ls = [v[1] for v in ls if v[1] not in columns]  # 許容されないカラムを抽出
        if err_ls:
            raise ValueError(
                "[{}] is unacceptable for order_by param.".format(ls[0][1])
            )

        ls = [(desc(v[1]) if v[0] == "-" else asc(v[1])) for v in ls]  # 符号をasc/descに変換
        self.sort = ls
        self.limit = limit
        self.offset = offset
        self.filter = []

    def append_filter(self, elem: FunctionElement) -> None:
        self.filter.append(elem)

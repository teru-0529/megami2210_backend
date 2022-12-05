#!/usr/bin/python3
# base.py

from fastapi import Query
from pydantic import BaseModel, Field

# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+

# クエリパラメータ
q_offset: Query = Query(
    default=0,
    title="Offset of result data",
    description="結果抽出時のオフセット値",
    ge=0,
    example=0,
)

q_limit: Query = Query(
    default=10,
    title="Limit of result data",
    description="結果抽出時の最大件数",
    ge=1,
    le=1000,
    example=10,
)


def q_sort(default: str, example: str) -> Query:
    return Query(
        default=default,
        title="Sort condition",
        description="ソートキー ※[+deadline,-asaignee_id] のように複数指定可能。+:ASC、-:DESC",
        regex="^[\+\-][a-z\_]+(?:,[\+\-][a-z\_]+)*$",  # noqa: W605
        example=example,
    )


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class CoreModel(BaseModel):
    pass


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class Message(BaseModel):
    detail: str = Field(title="detail", description="メッセージ", example="サーバーエラーです。")


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class QueryModel(BaseModel):
    count: int = Field(
        title="Record count", description="検索条件に合致するレコード件数", ge=0, example=1
    )

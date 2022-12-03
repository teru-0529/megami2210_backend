#!/usr/bin/python3
# base.py

from fastapi import Query
from pydantic import BaseModel, Field

# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+

# クエリパラメータ
q_offset: int = Query(
    default=0,
    title="Offset of result data",
    description="結果抽出時のオフセット値",
    ge=0,
    example=0,
)

q_limit: int = Query(
    default=10,
    title="Limit of result data",
    description="結果抽出時の最大件数",
    ge=1,
    le=1000,
    example=10,
)

q_sort: str = Query(
    default="+id",
    title="Sort condition",
    description="ソートキー ※[+deadline,-asaignee_id] のように複数指定可能。+:ASC、-:DESC",
    regex="^[\+\-][a-z\_]+(?:,[\+\-][a-z\_]+)*$",  # noqa: W605
    example="+deadline,-id",
)

# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class CoreModel(BaseModel):
    pass


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class IDModelMixin(BaseModel):
    id: int = Field(title="Id", description="リソースのユニーク性を担保するID", ge=1, example=10)


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class Message(BaseModel):
    detail: str = Field(title="detail", description="メッセージ", example="サーバーエラーです。")


# ----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+


class QueryModel(BaseModel):
    count: int = Field(
        title="Record count", description="検索条件に合致するレコード件数", ge=0, example=1
    )

#!/usr/bin/python3
# base.py

from pydantic import BaseModel, Field


class CoreModel(BaseModel):
    pass


class IDModelMixin(BaseModel):
    id: int = Field(title="Id", description="リソースのユニーク性を担保するID", ge=1, example=10)

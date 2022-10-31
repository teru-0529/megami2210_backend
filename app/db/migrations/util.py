#!/usr/bin/python3
# util.py

from typing import Tuple
import sqlalchemy as sa


def timestamps(indexed: bool = False) -> Tuple[sa.Column, sa.Column]:
    return (
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            index=indexed,
            comment="登録日時",
        ),
        sa.Column(
            "modified_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            index=indexed,
            comment="更新日時",
        ),
    )

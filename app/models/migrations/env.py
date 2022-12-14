import logging
import os
import pathlib
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

sys.path.append(str(pathlib.Path(__file__).resolve().parents[3]))
from app.core.config import SYNC_URL  # noqa:E402

config = context.config
fileConfig(config.config_file_name)
logger = logging.getLogger("alembic.env")


def run_migrations_online() -> None:
    CONTAINER_DSN = os.environ.get("CONTAINER_DSN", "")
    DB_URL = CONTAINER_DSN if CONTAINER_DSN else SYNC_URL

    logger.info("Run migrate on {0}".format(str(DB_URL)))

    connectable = config.attributes.get("connection", None)
    config.set_main_option("sqlalchemy.url", str(DB_URL))

    if connectable is None:
        connectable = engine_from_config(
            config.get_section(config.config_ini_section),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=None)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()

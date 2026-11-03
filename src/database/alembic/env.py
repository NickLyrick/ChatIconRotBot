"""Alembic environment: runs migrations against DATABASE_URL over asyncpg."""

import asyncio
import os
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from src.database.schemas import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# The URL is never stored in alembic.ini: it carries the database password.
database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise RuntimeError("DATABASE_URL is not set; Alembic has no database to migrate")
config.set_main_option("sqlalchemy.url", database_url)

# Options shared by offline and online runs.
CONFIGURE_OPTIONS = {
    "target_metadata": target_metadata,
    "compare_type": True,
    "compare_server_default": True,
}


def run_migrations_offline() -> None:
    """Emit the migration SQL to stdout instead of running it."""

    context.configure(
        url=database_url,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        **CONFIGURE_OPTIONS,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run the migrations over an open connection."""

    context.configure(connection=connection, **CONFIGURE_OPTIONS)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Open an async engine and run the migrations through it."""

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_async_migrations())

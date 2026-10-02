from logging.config import fileConfig
import os

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import create_engine, pool
from sqlalchemy.engine import URL


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

load_dotenv()

target_metadata = None


def get_database_url():
    """Build an SQLAlchemy URL from the application's database settings."""

    database_url = os.getenv("DATABASE_URL")
    if database_url:
        if database_url.startswith("postgres://"):
            return database_url.replace(
                "postgres://", "postgresql+psycopg2://", 1
            )
        if database_url.startswith("postgresql://"):
            return database_url.replace(
                "postgresql://", "postgresql+psycopg2://", 1
            )
        return database_url

    variable_names = ("DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD")
    values = {name: os.getenv(name) for name in variable_names}
    missing = [name for name, value in values.items() if not value]

    if missing:
        raise RuntimeError(
            "Missing database environment variables: " + ", ".join(missing)
        )

    try:
        port = int(values["DB_PORT"])
    except ValueError as error:
        raise RuntimeError("DB_PORT must be an integer.") from error

    return URL.create(
        drivername="postgresql+psycopg2",
        username=values["DB_USER"],
        password=values["DB_PASSWORD"],
        host=values["DB_HOST"],
        port=port,
        database=values["DB_NAME"],
    )


def run_migrations_offline():
    """Generate migration SQL without opening a database connection."""

    context.configure(
        url=get_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations against the configured PostgreSQL database."""

    connectable = create_engine(get_database_url(), poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

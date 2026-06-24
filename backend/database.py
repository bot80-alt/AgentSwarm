import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

BACKEND_DIR = Path(__file__).resolve().parent
REPO_ROOT = BACKEND_DIR.parent

load_dotenv(REPO_ROOT / ".env")
load_dotenv(BACKEND_DIR / ".env")

DEFAULT_DB_PATH = REPO_ROOT / "agent_marketplace.db"
DEFAULT_SQLITE_URL = f"sqlite:///{DEFAULT_DB_PATH.as_posix()}"


def _resolve_database_url() -> str:
    raw_url = os.getenv("DATABASE_URL", DEFAULT_SQLITE_URL).strip()
    if raw_url.startswith("postgres://"):
        raw_url = raw_url.replace("postgres://", "postgresql+psycopg://", 1)
    if raw_url.startswith("sqlite:///./"):
        relative_name = raw_url.removeprefix("sqlite:///./")
        raw_url = f"sqlite:///{(REPO_ROOT / relative_name).as_posix()}"
    return raw_url


DATABASE_URL = _resolve_database_url()

engine_kwargs: dict[str, object] = {}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    **engine_kwargs,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def migrate_schema() -> None:
    """Add swarm node config columns to existing SQLite databases."""
    if not DATABASE_URL.startswith("sqlite"):
        return

    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    if "workflow_node_runs" not in inspector.get_table_names():
        return

    existing = {column["name"] for column in inspector.get_columns("workflow_node_runs")}
    additions = {
        "task": "TEXT NOT NULL DEFAULT ''",
        "persona": "TEXT NOT NULL DEFAULT ''",
        "configured_model": "TEXT NOT NULL DEFAULT 'gpt-4o-mini'",
        "execution_mode": "TEXT NOT NULL DEFAULT 'parallel'",
    }

    with engine.begin() as connection:
        for column_name, ddl in additions.items():
            if column_name not in existing:
                connection.execute(
                    text(f"ALTER TABLE workflow_node_runs ADD COLUMN {column_name} {ddl}")
                )


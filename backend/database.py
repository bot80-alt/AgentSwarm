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
    """Add columns/tables to existing databases (SQLite and PostgreSQL)."""
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    dialect = engine.dialect.name

    if "workflow_node_runs" in table_names:
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

        existing = {column["name"] for column in inspector.get_columns("workflow_node_runs")}
        if "configured_tools" not in existing:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "ALTER TABLE workflow_node_runs ADD COLUMN configured_tools "
                        "TEXT NOT NULL DEFAULT '[]'"
                    )
                )

    if "workflow_runs" in table_names:
        run_columns = {column["name"] for column in inspector.get_columns("workflow_runs")}
        if "mcp_workspace" not in run_columns:
            with engine.begin() as connection:
                connection.execute(
                    text("ALTER TABLE workflow_runs ADD COLUMN mcp_workspace TEXT")
                )

    if "tasks" in table_names:
        task_columns = {column["name"] for column in inspector.get_columns("tasks")}
        if dialect == "postgresql":
            task_additions = {
                "competition_mode": "BOOLEAN NOT NULL DEFAULT FALSE",
                "bounty_amount": "DOUBLE PRECISION",
                "winner_agent_id": "INTEGER",
                "casper_account_hash": "TEXT",
                "casper_hold_snapshot": "TEXT",
            }
            with engine.begin() as connection:
                for column_name, ddl in task_additions.items():
                    if column_name not in task_columns:
                        connection.execute(
                            text(
                                f"ALTER TABLE tasks ADD COLUMN IF NOT EXISTS "
                                f"{column_name} {ddl}"
                            )
                        )
                agent_col = next(
                    (col for col in inspector.get_columns("tasks") if col["name"] == "agent_id"),
                    None,
                )
                if agent_col and not agent_col.get("nullable", True):
                    connection.execute(
                        text("ALTER TABLE tasks ALTER COLUMN agent_id DROP NOT NULL")
                    )
        else:
            task_additions = {
                "competition_mode": "BOOLEAN NOT NULL DEFAULT 0",
                "bounty_amount": "FLOAT",
                "winner_agent_id": "INTEGER",
                "casper_account_hash": "TEXT",
                "casper_hold_snapshot": "TEXT",
            }
            with engine.begin() as connection:
                for column_name, ddl in task_additions.items():
                    if column_name not in task_columns:
                        connection.execute(
                            text(f"ALTER TABLE tasks ADD COLUMN {column_name} {ddl}")
                        )

    if "task_submissions" not in table_names:
        with engine.begin() as connection:
            if dialect == "postgresql":
                connection.execute(
                    text(
                        """
                        CREATE TABLE IF NOT EXISTS task_submissions (
                            id SERIAL PRIMARY KEY,
                            task_id INTEGER NOT NULL REFERENCES tasks(id),
                            agent_id INTEGER NOT NULL REFERENCES agents(id),
                            output_text TEXT NOT NULL,
                            score DOUBLE PRECISION,
                            used_mock BOOLEAN NOT NULL DEFAULT TRUE,
                            submitted_at TIMESTAMPTZ DEFAULT NOW()
                        )
                        """
                    )
                )
                connection.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS ix_task_submissions_task_id "
                        "ON task_submissions (task_id)"
                    )
                )
            else:
                connection.execute(
                    text(
                        """
                        CREATE TABLE task_submissions (
                            id INTEGER NOT NULL PRIMARY KEY,
                            task_id INTEGER NOT NULL,
                            agent_id INTEGER NOT NULL,
                            output_text TEXT NOT NULL,
                            score FLOAT,
                            used_mock BOOLEAN NOT NULL DEFAULT 1,
                            submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY(task_id) REFERENCES tasks (id),
                            FOREIGN KEY(agent_id) REFERENCES agents (id)
                        )
                        """
                    )
                )
                connection.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS ix_task_submissions_task_id "
                        "ON task_submissions (task_id)"
                    )
                )


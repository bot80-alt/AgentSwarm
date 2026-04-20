from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "agent_marketplace.db"
DATABASE_URL = f"sqlite:///{DEFAULT_DB_PATH.as_posix()}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

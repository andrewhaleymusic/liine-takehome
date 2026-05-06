from pathlib import Path

from sqlalchemy.engine import Connection, Engine

from app.db import models  # noqa: F401
from app.db.base import Base


def ensure_sqlite_parent_dir(database_url: str) -> None:
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        return

    db_path = Path(database_url.removeprefix(prefix))
    if db_path.parent:
        db_path.parent.mkdir(parents=True, exist_ok=True)


def create_tables(bind: Engine | Connection) -> None:
    Base.metadata.create_all(bind=bind)

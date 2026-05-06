from pathlib import Path


def ensure_sqlite_parent_dir(database_url: str) -> None:
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        return

    db_path = Path(database_url.removeprefix(prefix))
    if db_path.parent:
        db_path.parent.mkdir(parents=True, exist_ok=True)

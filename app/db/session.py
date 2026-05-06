from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


def get_engine(*, test: bool = False) -> Engine:
    settings = get_settings()
    return create_engine(
        settings.database_url_for(test=test),
        future=True,
        connect_args={"check_same_thread": False},
    )


def get_session_factory(*, test: bool = False) -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(test=test), autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()

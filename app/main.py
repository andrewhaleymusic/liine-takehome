from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.core.config import get_settings
from app.db.init_db import create_tables, ensure_sqlite_parent_dir
from app.db.session import build_engine


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    ensure_sqlite_parent_dir(settings.database_url)
    engine = build_engine(settings.database_url)
    create_tables(engine)
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Liine Take Home", lifespan=lifespan)
    app.include_router(router)
    return app


app = create_app()

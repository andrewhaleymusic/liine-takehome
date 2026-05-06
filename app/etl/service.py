import logging

from app.core.config import Settings
from app.db.init_db import ensure_sqlite_parent_dir

logger = logging.getLogger(__name__)


def run_etl(settings: Settings) -> int:
    ensure_sqlite_parent_dir(settings.database_url)
    logger.error("ETL has not been implemented yet. Prompt 3 owns this work.")
    return 2

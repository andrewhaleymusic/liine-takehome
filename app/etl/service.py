import logging
from dataclasses import dataclass

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.init_db import create_tables, ensure_sqlite_parent_dir
from app.db.session import build_engine
from app.etl.loader import ETLValidationError, replace_restaurant_schedule, truncate_runtime_data
from app.etl.parser import ETLParseError, parse_schedule_row, read_csv_rows

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ETLReport:
    total_rows: int
    successful_rows: int
    failed_rows: int
    written_intervals: int


def execute_etl(settings: Settings, *, truncate: bool = False) -> ETLReport:
    ensure_sqlite_parent_dir(settings.database_url)
    raw_rows = read_csv_rows(settings.csv_path)
    engine = build_engine(settings.database_url)
    create_tables(engine)

    if truncate:
        with Session(engine) as session:
            truncate_runtime_data(session)
            session.commit()

    total_rows = 0
    successful_rows = 0
    failed_rows = 0
    written_intervals = 0

    for raw_row in raw_rows:
        total_rows += 1
        try:
            parsed_schedule = parse_schedule_row(
                raw_row.row_number, raw_row.name, raw_row.hours_text
            )
            with Session(engine) as session:
                normalized = replace_restaurant_schedule(session, parsed_schedule)
                session.commit()
            successful_rows += 1
            written_intervals += len(normalized.intervals)
        except ETLParseError as exc:
            failed_rows += 1
            logger.error("%s", exc)
        except (ETLValidationError, SQLAlchemyError) as exc:
            failed_rows += 1
            logger.error(
                "Row %s (%s): %s. Raw hours: %s",
                raw_row.row_number,
                raw_row.name.strip(),
                exc,
                raw_row.hours_text.strip(),
            )

    logger.info(
        "ETL complete: total_rows=%s successful_rows=%s failed_rows=%s written_intervals=%s",
        total_rows,
        successful_rows,
        failed_rows,
        written_intervals,
    )
    return ETLReport(
        total_rows=total_rows,
        successful_rows=successful_rows,
        failed_rows=failed_rows,
        written_intervals=written_intervals,
    )


def run_etl(settings: Settings, *, truncate: bool = False) -> int:
    try:
        report = execute_etl(settings, truncate=truncate)
    except (ETLParseError, OSError, SQLAlchemyError) as exc:
        logger.error("ETL failed before row processing began: %s", exc)
        return 2

    if report.failed_rows > 0:
        return 1
    return 0

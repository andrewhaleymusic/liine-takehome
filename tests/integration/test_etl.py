from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.models import OpeningIntervalModel, Restaurant
from app.db.session import build_engine
from app.etl.service import execute_etl

CSV_HEADER = '"Restaurant Name","Hours"\n'


def make_settings(tmp_path: Path, csv_body: str) -> Settings:
    csv_path = tmp_path / "restaurants.csv"
    csv_path.write_text(CSV_HEADER + csv_body, encoding="utf-8")
    database_path = tmp_path / "restaurants.db"
    return Settings(
        database_url=f"sqlite:///{database_path}",
        test_database_url=f"sqlite:///{tmp_path / 'test.db'}",
        csv_path=csv_path,
    )


def fetch_restaurant_names(settings: Settings) -> list[str]:
    engine = build_engine(settings.database_url)
    with Session(engine) as session:
        return list(session.scalars(select(Restaurant.name).order_by(Restaurant.name)))


def fetch_intervals(settings: Settings, restaurant_name: str) -> list[tuple[int, int]]:
    engine = build_engine(settings.database_url)
    with Session(engine) as session:
        restaurant = session.scalar(select(Restaurant).where(Restaurant.name == restaurant_name))
        assert restaurant is not None
        rows = session.scalars(
            select(OpeningIntervalModel)
            .where(OpeningIntervalModel.restaurant_id == restaurant.id)
            .order_by(OpeningIntervalModel.start_minute, OpeningIntervalModel.end_minute)
        )
        return [(row.start_minute, row.end_minute) for row in rows]


def test_execute_etl_writes_happy_path_row(tmp_path: Path) -> None:
    settings = make_settings(tmp_path, '"Happy Path","Mon 11 am - 1 pm"\n')

    report = execute_etl(settings)

    assert report.total_rows == 1
    assert report.successful_rows == 1
    assert report.failed_rows == 0
    assert fetch_restaurant_names(settings) == ["Happy Path"]
    assert fetch_intervals(settings, "Happy Path") == [(660, 780)]


def test_execute_etl_rejects_day_overlap_and_writes_nothing(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    settings = make_settings(
        tmp_path,
        '"Overlap Spot","Mon-Wed 5 pm - 9 pm / Wednesday-Saturday 6 pm to 10 pm"\n',
    )

    report = execute_etl(settings)

    assert report.total_rows == 1
    assert report.successful_rows == 0
    assert report.failed_rows == 1
    assert fetch_restaurant_names(settings) == []
    assert "overlapping intervals" in caplog.text
    assert "Wednesday-Saturday 6 pm to 10 pm" in caplog.text


def test_execute_etl_rejects_week_wrap_overlap_and_writes_nothing(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    settings = make_settings(tmp_path, '"Wrap Overlap","Sun 11 pm - 2 am / Mon 1 am - 3 am"\n')

    report = execute_etl(settings)

    assert report.total_rows == 1
    assert report.successful_rows == 0
    assert report.failed_rows == 1
    assert fetch_restaurant_names(settings) == []
    assert "overlapping intervals" in caplog.text
    assert "Sun 11 pm - 2 am / Mon 1 am - 3 am" in caplog.text


def test_execute_etl_writes_week_wrap_row(tmp_path: Path) -> None:
    settings = make_settings(tmp_path, '"Late Spot","Sun 12 pm - 2 am"\n')

    report = execute_etl(settings)

    assert report.successful_rows == 1
    assert fetch_intervals(settings, "Late Spot") == [(0, 120), (9360, 10080)]


def test_execute_etl_continues_after_bad_row(tmp_path: Path) -> None:
    settings = make_settings(
        tmp_path,
        '"Bad Row","Mon-Wed 5 pm - 9 pm / Wednesday-Saturday 6 pm to 10 pm"\n'
        '"Good Row","Mon 11 am - 1 pm"\n',
    )

    report = execute_etl(settings)

    assert report.total_rows == 2
    assert report.successful_rows == 1
    assert report.failed_rows == 1
    assert fetch_restaurant_names(settings) == ["Good Row"]
    assert fetch_intervals(settings, "Good Row") == [(660, 780)]


def test_execute_etl_is_idempotent_without_truncate(tmp_path: Path) -> None:
    settings = make_settings(tmp_path, '"Repeatable","Mon 11 am - 1 pm"\n')

    first_report = execute_etl(settings)
    second_report = execute_etl(settings)

    assert first_report.successful_rows == 1
    assert second_report.successful_rows == 1
    assert fetch_restaurant_names(settings) == ["Repeatable"]
    assert fetch_intervals(settings, "Repeatable") == [(660, 780)]


def test_execute_etl_truncate_replaces_existing_database_contents(tmp_path: Path) -> None:
    settings = make_settings(tmp_path, '"First","Mon 11 am - 1 pm"\n')
    execute_etl(settings)

    settings.csv_path.write_text(
        CSV_HEADER + '"Second","Tue 2 pm - 4 pm"\n',
        encoding="utf-8",
    )

    report = execute_etl(settings, truncate=True)

    assert report.successful_rows == 1
    assert fetch_restaurant_names(settings) == ["Second"]
    assert fetch_intervals(settings, "Second") == [(2280, 2400)]

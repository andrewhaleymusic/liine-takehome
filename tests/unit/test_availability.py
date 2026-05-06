from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.db.init_db import create_tables
from app.db.models import OpeningIntervalModel, Restaurant
from app.db.session import build_engine
from app.services.availability import find_open_restaurants, local_datetime_to_minute_of_week


def seed_restaurant(
    session: Session,
    *,
    name: str,
    intervals: list[tuple[int, int]],
) -> None:
    restaurant = Restaurant(name=name)
    session.add(restaurant)
    session.flush()
    for start_minute, end_minute in intervals:
        session.add(
            OpeningIntervalModel(
                restaurant_id=restaurant.id,
                start_minute=start_minute,
                end_minute=end_minute,
            )
        )
    session.commit()


def test_local_datetime_to_minute_of_week_uses_monday_zero_convention() -> None:
    requested_datetime = datetime(2026, 5, 6, 11, 30, 0)

    assert local_datetime_to_minute_of_week(requested_datetime) == 3570


def test_find_open_restaurants_respects_open_and_close_boundaries(tmp_path) -> None:
    engine = build_engine(f"sqlite:///{tmp_path / 'availability.db'}")
    create_tables(engine)

    with Session(engine) as session:
        seed_restaurant(session, name="Alpha", intervals=[(660, 780)])
        seed_restaurant(session, name="Bravo", intervals=[(780, 900)])

    with Session(engine) as session:
        assert find_open_restaurants(session, datetime(2026, 5, 4, 11, 0, 0)) == ["Alpha"]
        assert find_open_restaurants(session, datetime(2026, 5, 4, 12, 59, 0)) == ["Alpha"]
        assert find_open_restaurants(session, datetime(2026, 5, 4, 13, 0, 0)) == ["Bravo"]
        assert find_open_restaurants(session, datetime(2026, 5, 4, 15, 0, 0)) == []


def test_find_open_restaurants_returns_names_alphabetically(tmp_path) -> None:
    engine = build_engine(f"sqlite:///{tmp_path / 'ordering.db'}")
    create_tables(engine)

    with Session(engine) as session:
        seed_restaurant(session, name="Zulu", intervals=[(660, 780)])
        seed_restaurant(session, name="Alpha", intervals=[(660, 780)])

    with Session(engine) as session:
        assert find_open_restaurants(session, datetime(2026, 5, 4, 11, 30, 0)) == [
            "Alpha",
            "Zulu",
        ]


def test_find_open_restaurants_supports_week_wrap_intervals(tmp_path) -> None:
    engine = build_engine(f"sqlite:///{tmp_path / 'weekwrap.db'}")
    create_tables(engine)

    with Session(engine) as session:
        seed_restaurant(session, name="Late Spot", intervals=[(0, 120), (9360, 10080)])

    with Session(engine) as session:
        assert find_open_restaurants(session, datetime(2026, 5, 10, 13, 0, 0)) == ["Late Spot"]
        assert find_open_restaurants(session, datetime(2026, 5, 11, 1, 0, 0)) == ["Late Spot"]

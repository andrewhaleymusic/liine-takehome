import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.init_db import create_tables
from app.db.models import OpeningIntervalModel, Restaurant


def test_create_tables_builds_prompt_2_schema() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)

    create_tables(engine)

    inspector = inspect(engine)
    assert sorted(inspector.get_table_names()) == ["opening_intervals", "restaurants"]


def test_opening_interval_constraints_reject_invalid_range() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_tables(engine)

    with Session(engine) as session:
        restaurant = Restaurant(name="Test Restaurant")
        session.add(restaurant)
        session.flush()

        session.add(
            OpeningIntervalModel(
                restaurant_id=restaurant.id,
                start_minute=500,
                end_minute=500,
            )
        )

        with pytest.raises(IntegrityError):
            session.commit()

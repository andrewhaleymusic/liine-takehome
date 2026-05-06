from __future__ import annotations

from datetime import datetime

from sqlalchemy import distinct, select
from sqlalchemy.orm import Session

from app.db.models import OpeningIntervalModel, Restaurant
from app.domain.intervals import minute_of_week


def local_datetime_to_minute_of_week(local_datetime: datetime) -> int:
    return minute_of_week(
        day_of_week=local_datetime.weekday(),
        hour=local_datetime.hour,
        minute=local_datetime.minute,
    )


def find_open_restaurants(session: Session, local_datetime: datetime) -> list[str]:
    requested_minute = local_datetime_to_minute_of_week(local_datetime)
    statement = (
        select(distinct(Restaurant.name))
        .join(OpeningIntervalModel, OpeningIntervalModel.restaurant_id == Restaurant.id)
        .where(OpeningIntervalModel.start_minute <= requested_minute)
        .where(requested_minute < OpeningIntervalModel.end_minute)
        .order_by(Restaurant.name)
    )
    return list(session.scalars(statement))

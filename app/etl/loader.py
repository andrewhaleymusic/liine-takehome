from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models import OpeningIntervalModel, Restaurant
from app.domain.intervals import MINUTES_PER_WEEK, OpeningInterval, minute_of_week
from app.etl.parser import ParsedDaySpec, ParsedRestaurantSchedule, ParsedTime, ParsedTimeRange


class ETLValidationError(ValueError):
    """Raised when parsed schedule data violates storage rules."""


@dataclass(frozen=True, slots=True)
class NormalizedRestaurantSchedule:
    row_number: int
    name: str
    hours_text: str
    intervals: tuple[OpeningInterval, ...]


def normalize_schedule(schedule: ParsedRestaurantSchedule) -> NormalizedRestaurantSchedule:
    intervals: list[OpeningInterval] = []
    for segment in schedule.segments:
        for day_spec in segment.day_specs:
            for day in expand_day_spec(day_spec):
                intervals.extend(normalize_day_and_time(day, segment.time_range))

    deduped_intervals = dedupe_intervals(intervals)
    validate_no_overlaps(schedule.name, deduped_intervals)

    return NormalizedRestaurantSchedule(
        row_number=schedule.row_number,
        name=schedule.name,
        hours_text=schedule.hours_text,
        intervals=tuple(deduped_intervals),
    )


def expand_day_spec(day_spec: ParsedDaySpec) -> tuple[int, ...]:
    if day_spec.start_day <= day_spec.end_day:
        return tuple(range(day_spec.start_day, day_spec.end_day + 1))

    return tuple(range(day_spec.start_day, 7)) + tuple(range(0, day_spec.end_day + 1))


def normalize_day_and_time(day: int, time_range: ParsedTimeRange) -> list[OpeningInterval]:
    start_minute = minute_of_week(day, time_range.start.hour, time_range.start.minute)
    end_is_same_day = parsed_time_tuple(time_range.end) > parsed_time_tuple(time_range.start)
    if end_is_same_day:
        end_minute = minute_of_week(day, time_range.end.hour, time_range.end.minute)
        return [OpeningInterval(start_minute=start_minute, end_minute=end_minute)]

    if day < 6:
        end_minute = minute_of_week(day + 1, time_range.end.hour, time_range.end.minute)
        return [OpeningInterval(start_minute=start_minute, end_minute=end_minute)]

    wrapped_end_minute = minute_of_week(0, time_range.end.hour, time_range.end.minute)
    wrapped_intervals = [OpeningInterval(start_minute=start_minute, end_minute=MINUTES_PER_WEEK)]
    if wrapped_end_minute > 0:
        wrapped_intervals.append(OpeningInterval(start_minute=0, end_minute=wrapped_end_minute))
    return wrapped_intervals


def parsed_time_tuple(parsed_time: ParsedTime) -> tuple[int, int]:
    return parsed_time.hour, parsed_time.minute


def dedupe_intervals(intervals: list[OpeningInterval]) -> list[OpeningInterval]:
    deduped: list[OpeningInterval] = []
    seen: set[tuple[int, int]] = set()
    for interval in sorted(intervals, key=lambda item: (item.start_minute, item.end_minute)):
        key = (interval.start_minute, interval.end_minute)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(interval)
    return deduped


def validate_no_overlaps(restaurant_name: str, intervals: list[OpeningInterval]) -> None:
    ordered_intervals = sorted(intervals, key=lambda item: (item.start_minute, item.end_minute))
    for current, following in zip(ordered_intervals, ordered_intervals[1:]):
        if current.overlaps(following):
            raise ETLValidationError(
                f"restaurant '{restaurant_name}' has overlapping intervals "
                f"[{current.start_minute}, {current.end_minute}) and "
                f"[{following.start_minute}, {following.end_minute})"
            )


def replace_restaurant_schedule(
    session: Session,
    schedule: ParsedRestaurantSchedule,
) -> NormalizedRestaurantSchedule:
    normalized = normalize_schedule(schedule)

    restaurant = session.scalar(select(Restaurant).where(Restaurant.name == normalized.name))
    if restaurant is None:
        restaurant = Restaurant(name=normalized.name)
        session.add(restaurant)
        session.flush()

    session.execute(
        delete(OpeningIntervalModel).where(OpeningIntervalModel.restaurant_id == restaurant.id)
    )

    for interval in normalized.intervals:
        session.add(
            OpeningIntervalModel(
                restaurant_id=restaurant.id,
                start_minute=interval.start_minute,
                end_minute=interval.end_minute,
            )
        )

    session.flush()
    return normalized


def truncate_runtime_data(session: Session) -> None:
    session.execute(delete(OpeningIntervalModel))
    session.execute(delete(Restaurant))

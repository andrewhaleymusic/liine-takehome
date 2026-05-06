import pytest

from app.etl.loader import ETLValidationError, normalize_schedule
from app.etl.parser import parse_schedule_row


def test_normalize_schedule_splits_week_wrap_interval() -> None:
    schedule = parse_schedule_row(1, "Late Spot", "Sun 12 pm - 2 am")

    normalized = normalize_schedule(schedule)

    assert [(interval.start_minute, interval.end_minute) for interval in normalized.intervals] == [
        (0, 120),
        (9360, 10080),
    ]


def test_normalize_schedule_rejects_day_overlap() -> None:
    schedule = parse_schedule_row(
        1,
        "Overlap Spot",
        "Mon-Wed 5 pm - 9 pm / Wednesday-Saturday 6 pm to 10 pm",
    )

    with pytest.raises(ETLValidationError):
        normalize_schedule(schedule)


def test_normalize_schedule_allows_adjacent_intervals() -> None:
    schedule = parse_schedule_row(1, "Adjacent Spot", "Mon 5 pm - 9 pm / Mon 9 pm - 10 pm")

    normalized = normalize_schedule(schedule)

    assert [(interval.start_minute, interval.end_minute) for interval in normalized.intervals] == [
        (1020, 1260),
        (1260, 1320),
    ]


def test_normalize_schedule_deduplicates_identical_intervals() -> None:
    schedule = parse_schedule_row(1, "Duplicate Spot", "Mon 5 pm - 9 pm / Mon 5 pm - 9 pm")

    normalized = normalize_schedule(schedule)

    assert [(interval.start_minute, interval.end_minute) for interval in normalized.intervals] == [
        (1020, 1260),
    ]

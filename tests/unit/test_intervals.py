import pytest

from app.domain.intervals import MINUTES_PER_WEEK, OpeningInterval, minute_of_week


def test_minute_of_week_returns_expected_offset() -> None:
    assert minute_of_week(0, 0, 0) == 0
    assert minute_of_week(2, 3, 15) == (2 * 24 * 60) + (3 * 60) + 15
    assert minute_of_week(6, 23, 59) == MINUTES_PER_WEEK - 1


@pytest.mark.parametrize(
    ("day_of_week", "hour", "minute"),
    [
        (-1, 12, 0),
        (7, 12, 0),
        (0, -1, 0),
        (0, 24, 0),
        (0, 12, -1),
        (0, 12, 60),
    ],
)
def test_minute_of_week_rejects_out_of_bounds_values(
    day_of_week: int,
    hour: int,
    minute: int,
) -> None:
    with pytest.raises(ValueError):
        minute_of_week(day_of_week, hour, minute)


@pytest.mark.parametrize(
    ("start_minute", "end_minute"),
    [
        (-1, 10),
        (MINUTES_PER_WEEK, MINUTES_PER_WEEK),
        (10, 10),
        (10, 9),
        (0, 0),
        (0, MINUTES_PER_WEEK + 1),
    ],
)
def test_opening_interval_rejects_invalid_bounds(start_minute: int, end_minute: int) -> None:
    with pytest.raises(ValueError):
        OpeningInterval(start_minute=start_minute, end_minute=end_minute)


def test_opening_interval_overlaps_when_ranges_intersect() -> None:
    left = OpeningInterval(start_minute=100, end_minute=200)
    right = OpeningInterval(start_minute=150, end_minute=250)

    assert left.overlaps(right) is True
    assert right.overlaps(left) is True


def test_opening_interval_does_not_overlap_when_adjacent() -> None:
    left = OpeningInterval(start_minute=100, end_minute=200)
    right = OpeningInterval(start_minute=200, end_minute=300)

    assert left.overlaps(right) is False
    assert left.is_adjacent_to(right) is True


def test_opening_interval_does_not_overlap_when_separate() -> None:
    left = OpeningInterval(start_minute=100, end_minute=200)
    right = OpeningInterval(start_minute=250, end_minute=300)

    assert left.overlaps(right) is False
    assert left.is_adjacent_to(right) is False

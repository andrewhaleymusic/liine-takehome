from dataclasses import dataclass

MINUTES_PER_HOUR = 60
HOURS_PER_DAY = 24
DAYS_PER_WEEK = 7
MINUTES_PER_DAY = HOURS_PER_DAY * MINUTES_PER_HOUR
MINUTES_PER_WEEK = DAYS_PER_WEEK * MINUTES_PER_DAY


def minute_of_week(day_of_week: int, hour: int, minute: int) -> int:
    if not 0 <= day_of_week < DAYS_PER_WEEK:
        raise ValueError(f"day_of_week must be in [0, {DAYS_PER_WEEK - 1}]")
    if not 0 <= hour < HOURS_PER_DAY:
        raise ValueError(f"hour must be in [0, {HOURS_PER_DAY - 1}]")
    if not 0 <= minute < MINUTES_PER_HOUR:
        raise ValueError(f"minute must be in [0, {MINUTES_PER_HOUR - 1}]")

    return day_of_week * MINUTES_PER_DAY + hour * MINUTES_PER_HOUR + minute


@dataclass(frozen=True, slots=True)
class OpeningInterval:
    start_minute: int
    end_minute: int

    def __post_init__(self) -> None:
        if not 0 <= self.start_minute < MINUTES_PER_WEEK:
            raise ValueError(
                f"start_minute must be in [0, {MINUTES_PER_WEEK - 1}] for stored intervals"
            )
        if not 1 <= self.end_minute <= MINUTES_PER_WEEK:
            raise ValueError(f"end_minute must be in [1, {MINUTES_PER_WEEK}] for stored intervals")
        if self.start_minute >= self.end_minute:
            raise ValueError("stored intervals must satisfy start_minute < end_minute")

    def overlaps(self, other: "OpeningInterval") -> bool:
        return self.start_minute < other.end_minute and other.start_minute < self.end_minute

    def is_adjacent_to(self, other: "OpeningInterval") -> bool:
        return self.end_minute == other.start_minute or other.end_minute == self.start_minute

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

DAY_NAME_TO_INDEX = {
    "mon": 0,
    "monday": 0,
    "tue": 1,
    "tues": 1,
    "tuesday": 1,
    "wed": 2,
    "weds": 2,
    "wednesday": 2,
    "thu": 3,
    "thur": 3,
    "thurs": 3,
    "thursday": 3,
    "fri": 4,
    "friday": 4,
    "sat": 5,
    "saturday": 5,
    "sun": 6,
    "sunday": 6,
}


class ETLParseError(ValueError):
    """Raised when a row or token cannot be parsed into structured schedule data."""


@dataclass(frozen=True, slots=True)
class ParsedTime:
    hour: int
    minute: int


@dataclass(frozen=True, slots=True)
class ParsedDaySpec:
    start_day: int
    end_day: int

    @property
    def is_range(self) -> bool:
        return self.start_day != self.end_day


@dataclass(frozen=True, slots=True)
class ParsedTimeRange:
    start: ParsedTime
    end: ParsedTime


@dataclass(frozen=True, slots=True)
class ParsedScheduleSegment:
    day_specs: tuple[ParsedDaySpec, ...]
    time_range: ParsedTimeRange


@dataclass(frozen=True, slots=True)
class ParsedRestaurantSchedule:
    row_number: int
    name: str
    hours_text: str
    segments: tuple[ParsedScheduleSegment, ...]


def parse_csv_rows(csv_path: Path) -> list[ParsedRestaurantSchedule]:
    parsed_rows: list[ParsedRestaurantSchedule] = []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row_number, row in enumerate(reader, start=2):
            name = row.get("Restaurant Name")
            hours_text = row.get("Hours")
            if name is None or hours_text is None:
                raise ETLParseError(
                    f"CSV row {row_number} is missing required columns 'Restaurant Name' or 'Hours'"
                )
            parsed_rows.append(parse_schedule_row(row_number, name, hours_text))
    return parsed_rows


def parse_schedule_row(row_number: int, name: str, hours_text: str) -> ParsedRestaurantSchedule:
    normalized_name = name.strip()
    normalized_hours = hours_text.strip()

    if not normalized_name:
        raise ETLParseError(f"Row {row_number}: restaurant name must not be empty")
    if not normalized_hours:
        raise ETLParseError(f"Row {row_number} ({normalized_name}): hours text must not be empty")

    try:
        segments = tuple(
            parse_schedule_segment(segment) for segment in split_schedule_segments(hours_text)
        )
    except ETLParseError as exc:
        raise ETLParseError(
            f"Row {row_number} ({normalized_name}): {exc}. Raw hours: {normalized_hours}"
        ) from exc

    return ParsedRestaurantSchedule(
        row_number=row_number,
        name=normalized_name,
        hours_text=normalized_hours,
        segments=segments,
    )


def split_schedule_segments(hours_text: str) -> list[str]:
    segments = [segment.strip() for segment in hours_text.split("/") if segment.strip()]
    if not segments:
        raise ETLParseError("hours text did not contain any schedule segments")
    return segments


def parse_schedule_segment(segment_text: str) -> ParsedScheduleSegment:
    day_text, time_text = split_day_and_time_parts(segment_text)
    return ParsedScheduleSegment(
        day_specs=tuple(parse_day_group(day_text)),
        time_range=parse_time_range(time_text),
    )


def split_day_and_time_parts(segment_text: str) -> tuple[str, str]:
    text = segment_text.strip()

    first_digit_index = -1
    for index, character in enumerate(text):
        if character.isdigit():
            first_digit_index = index
            break

    if first_digit_index <= 0:
        raise ETLParseError(f"could not find a time range in segment '{segment_text.strip()}'")

    day_text = text[:first_digit_index].strip().rstrip(",")
    time_text = text[first_digit_index:].strip()

    if not day_text or not time_text:
        raise ETLParseError(f"segment '{segment_text.strip()}' is missing day or time content")

    return day_text, time_text


def parse_day_group(day_text: str) -> list[ParsedDaySpec]:
    parsed_specs: list[ParsedDaySpec] = []
    for token in [part.strip() for part in day_text.split(",")]:
        if not token:
            raise ETLParseError(f"day group '{day_text}' contains an empty token")
        parsed_specs.append(parse_day_spec(token))
    return parsed_specs


def parse_day_spec(token: str) -> ParsedDaySpec:
    if "-" in token:
        start_token, end_token = split_once(token, "-")
        start_day = parse_day_name(start_token)
        end_day = parse_day_name(end_token)
        return ParsedDaySpec(start_day=start_day, end_day=end_day)

    day_index = parse_day_name(token)
    return ParsedDaySpec(start_day=day_index, end_day=day_index)


def parse_day_name(token: str) -> int:
    normalized = normalize_token(token)
    try:
        return DAY_NAME_TO_INDEX[normalized]
    except KeyError as exc:
        raise ETLParseError(f"unknown day token '{token.strip()}'") from exc


def parse_time_range(time_text: str) -> ParsedTimeRange:
    normalized = " ".join(time_text.strip().split())
    if " to " in normalized.lower():
        start_token, end_token = split_once_case_insensitive(normalized, " to ")
    elif " - " in normalized:
        start_token, end_token = split_once(normalized, " - ")
    else:
        raise ETLParseError(f"time range '{time_text}' is missing a supported separator")

    return ParsedTimeRange(start=parse_time_token(start_token), end=parse_time_token(end_token))


def parse_time_token(token: str) -> ParsedTime:
    normalized = normalize_time_token(token)

    if normalized.endswith("am"):
        meridiem = "am"
        time_portion = normalized[:-2]
    elif normalized.endswith("pm"):
        meridiem = "pm"
        time_portion = normalized[:-2]
    else:
        raise ETLParseError(f"time token '{token.strip()}' is missing am/pm")

    if not time_portion:
        raise ETLParseError(f"time token '{token.strip()}' is missing an hour value")

    hour_text, minute_text = split_hour_and_minute(time_portion)
    hour = parse_int(hour_text, token)
    minute = parse_int(minute_text, token)

    if not 1 <= hour <= 12:
        raise ETLParseError(f"time token '{token.strip()}' has hour outside 1-12")
    if not 0 <= minute < 60:
        raise ETLParseError(f"time token '{token.strip()}' has minute outside 0-59")

    if meridiem == "am":
        hour = 0 if hour == 12 else hour
    else:
        hour = 12 if hour == 12 else hour + 12

    return ParsedTime(hour=hour, minute=minute)


def split_hour_and_minute(time_portion: str) -> tuple[str, str]:
    if ":" in time_portion:
        hour_text, minute_text = split_once(time_portion, ":")
        return hour_text, minute_text
    return time_portion, "0"


def parse_int(value: str, original_token: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise ETLParseError(
            f"time token '{original_token.strip()}' contains a non-numeric value"
        ) from exc


def normalize_time_token(token: str) -> str:
    return normalize_token(token).replace(".", "")


def normalize_token(token: str) -> str:
    return "".join(token.strip().lower().split())


def split_once(value: str, separator: str) -> tuple[str, str]:
    left, found_separator, right = value.partition(separator)
    if not found_separator:
        raise ETLParseError(f"value '{value}' is missing separator '{separator}'")
    return left.strip(), right.strip()


def split_once_case_insensitive(value: str, separator: str) -> tuple[str, str]:
    lowered_value = value.lower()
    lowered_separator = separator.lower()
    index = lowered_value.find(lowered_separator)
    if index == -1:
        raise ETLParseError(f"value '{value}' is missing separator '{separator.strip()}'")
    left = value[:index]
    right = value[index + len(separator) :]
    return left.strip(), right.strip()

import pytest

from app.etl.parser import (
    ETLParseError,
    ParsedDaySpec,
    ParsedTime,
    parse_schedule_row,
    parse_time_token,
)


def test_parse_schedule_row_parses_single_segment_for_all_days() -> None:
    parsed = parse_schedule_row(2, "The Cowfish Sushi Burger Bar", "Mon-Sun 11:00 am - 10 pm")

    assert parsed.name == "The Cowfish Sushi Burger Bar"
    assert parsed.hours_text == "Mon-Sun 11:00 am - 10 pm"
    assert len(parsed.segments) == 1
    assert parsed.segments[0].day_specs == (ParsedDaySpec(start_day=0, end_day=6),)
    assert parsed.segments[0].time_range.start == ParsedTime(hour=11, minute=0)
    assert parsed.segments[0].time_range.end == ParsedTime(hour=22, minute=0)


def test_parse_schedule_row_parses_multiple_segments_and_mixed_day_specs() -> None:
    parsed = parse_schedule_row(
        5,
        "Garland",
        "Tues-Fri, Sun 11:30 am - 10 pm  / Sat 5:30 pm - 11 pm",
    )

    assert len(parsed.segments) == 2

    first_segment = parsed.segments[0]
    assert first_segment.day_specs == (
        ParsedDaySpec(start_day=1, end_day=4),
        ParsedDaySpec(start_day=6, end_day=6),
    )
    assert first_segment.time_range.start == ParsedTime(hour=11, minute=30)
    assert first_segment.time_range.end == ParsedTime(hour=22, minute=0)

    second_segment = parsed.segments[1]
    assert second_segment.day_specs == (ParsedDaySpec(start_day=5, end_day=5),)
    assert second_segment.time_range.start == ParsedTime(hour=17, minute=30)
    assert second_segment.time_range.end == ParsedTime(hour=23, minute=0)


def test_parse_schedule_row_supports_full_day_names_and_to_separator() -> None:
    parsed = parse_schedule_row(
        10,
        "Example Restaurant",
        "Mon-Wed 5pm - 9pm / Wednesday-Saturday 6pm to 10pm",
    )

    assert len(parsed.segments) == 2
    assert parsed.segments[0].day_specs == (ParsedDaySpec(start_day=0, end_day=2),)
    assert parsed.segments[1].day_specs == (ParsedDaySpec(start_day=2, end_day=5),)
    assert parsed.segments[0].time_range.start == ParsedTime(hour=17, minute=0)
    assert parsed.segments[1].time_range.end == ParsedTime(hour=22, minute=0)


@pytest.mark.parametrize(
    ("token", "expected_hour", "expected_minute"),
    [
        ("12 am", 0, 0),
        ("12 pm", 12, 0),
        ("9:30 am", 9, 30),
        ("10pm", 22, 0),
    ],
)
def test_parse_time_token_handles_noon_midnight_and_compact_tokens(
    token: str,
    expected_hour: int,
    expected_minute: int,
) -> None:
    assert parse_time_token(token) == ParsedTime(hour=expected_hour, minute=expected_minute)


@pytest.mark.parametrize(
    "hours_text",
    [
        "Funday 11 am - 9 pm",
        "Mon-Sun 11 - 9 pm",
        "Mon-Sun eleven am - 9 pm",
        "Mon-Sun 11 am 9 pm",
    ],
)
def test_parse_schedule_row_rejects_malformed_input(hours_text: str) -> None:
    with pytest.raises(ETLParseError):
        parse_schedule_row(42, "Broken Restaurant", hours_text)


def test_parse_schedule_row_rejects_empty_name() -> None:
    with pytest.raises(ETLParseError):
        parse_schedule_row(42, "   ", "Mon-Sun 11 am - 9 pm")

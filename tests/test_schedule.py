"""Tests for :mod:`src.utility.schedule`: parsing and formatting chat settings."""

from datetime import date, datetime, timedelta, timezone

import pytest

from src.scheduler.runner import next_rotation_date
from src.utility.schedule import (
    MAX_DELTA_DAYS,
    available_hours,
    chat_today,
    day_label,
    describe_settings,
    example_rotation_date,
    format_chat_date,
    parse_delta,
    parse_rotation_date,
    rotation_at,
    upcoming_days,
    with_hour,
)

UTC = timezone.utc


# --- parse_rotation_date -------------------------------------------------------


def test_date_is_read_as_moscow_time_and_stored_in_utc():
    parsed = parse_rotation_date("31/12/2026 18:00")

    assert parsed == datetime(2026, 12, 31, 15, 0, tzinfo=UTC)
    assert parsed.utcoffset() == timedelta(0)


def test_surrounding_spaces_are_ignored():
    assert parse_rotation_date("  01/02/2027 00:30 ") == datetime(
        2027, 1, 31, 21, 30, tzinfo=UTC
    )


@pytest.mark.parametrize(
    "text",
    ["", "31.12.2026 18:00", "31/12/2026", "2026/12/31 18:00", "32/12/2026 18:00", "31/12/2026 25:00"],
)
def test_malformed_date_is_rejected(text):
    with pytest.raises(ValueError):
        parse_rotation_date(text)


# --- format_chat_date / example_rotation_date ---------------------------------


def test_stored_date_is_shown_in_moscow_time():
    assert format_chat_date(datetime(2026, 12, 31, 15, 0, tzinfo=UTC)) == "31.12.2026 18:00"


def test_parse_and_format_round_trip():
    assert format_chat_date(parse_rotation_date("05/03/2027 09:15")) == "05.03.2027 09:15"


def test_example_date_is_valid_and_in_the_future():
    now = datetime(2026, 12, 31, 22, 0, tzinfo=UTC)  # already 1 January in Moscow

    example = example_rotation_date(now)

    assert example == "02/01/2027 18:00"
    assert parse_rotation_date(example) > now


# --- parse_delta --------------------------------------------------------------


@pytest.mark.parametrize("text, expected", [("1", 1), (" 7 ", 7), (str(MAX_DELTA_DAYS), MAX_DELTA_DAYS)])
def test_valid_delta(text, expected):
    assert parse_delta(text) == expected


@pytest.mark.parametrize(
    "text", [None, "", "0", "-3", "3.5", "три", str(MAX_DELTA_DAYS + 1), "10000000000"]
)
def test_invalid_delta(text):
    assert parse_delta(text) is None


def test_largest_delta_keeps_the_scheduler_in_range():
    """A rotation set far ahead with the largest interval must not overflow."""

    scheduled = datetime(9998, 1, 1, tzinfo=UTC)

    assert next_rotation_date(scheduled, MAX_DELTA_DAYS, scheduled) == scheduled + timedelta(
        days=MAX_DELTA_DAYS
    )


# --- menu helpers -------------------------------------------------------------

# 15:30 in Moscow on Saturday, 7 November 2026.
NOW = datetime(2026, 11, 7, 12, 30, tzinfo=UTC)


def test_today_follows_moscow_not_utc():
    assert chat_today(datetime(2026, 11, 7, 21, 30, tzinfo=UTC)) == date(2026, 11, 8)


def test_rotation_at_is_moscow_hour_in_utc():
    assert rotation_at(date(2026, 11, 7), 18) == datetime(2026, 11, 7, 15, 0, tzinfo=UTC)


def test_only_future_hours_are_available_today():
    assert available_hours(date(2026, 11, 7), NOW) == list(range(16, 24))
    assert available_hours(date(2026, 11, 8), NOW) == list(range(24))
    assert available_hours(date(2026, 11, 6), NOW) == []


def test_upcoming_days_start_today():
    days = upcoming_days(NOW)

    assert days[0] == date(2026, 11, 7)
    assert days == [date(2026, 11, 7) + timedelta(days=i) for i in range(7)]


def test_upcoming_days_skip_today_after_the_last_hour():
    late = datetime(2026, 11, 7, 20, 30, tzinfo=UTC)  # 23:30 in Moscow

    days = upcoming_days(late)

    assert days[0] == date(2026, 11, 8)
    assert len(days) == 7


def test_with_hour_keeps_the_day_of_a_future_rotation():
    current = datetime(2026, 11, 10, 15, 0, tzinfo=UTC)  # 10.11 18:00 MSK

    assert format_chat_date(with_hour(current, 9, NOW)) == "10.11.2026 09:00"


def test_with_hour_moves_to_tomorrow_when_the_hour_has_passed_today():
    current = datetime(2026, 11, 7, 17, 0, tzinfo=UTC)  # today 20:00 MSK

    assert format_chat_date(with_hour(current, 10, NOW)) == "08.11.2026 10:00"


def test_with_hour_moves_an_overdue_rotation_to_today():
    overdue = datetime(2026, 11, 1, 15, 0, tzinfo=UTC)

    assert format_chat_date(with_hour(overdue, 20, NOW)) == "07.11.2026 20:00"


def test_with_hour_result_is_always_in_the_future():
    current = datetime(2026, 11, 7, 15, 0, tzinfo=UTC)

    for hour in range(24):
        assert with_hour(current, hour, NOW) > NOW


@pytest.mark.parametrize(
    "day, label",
    [
        (date(2026, 11, 7), "Сегодня"),
        (date(2026, 11, 8), "Завтра"),
        (date(2026, 11, 9), "Пн 09.11"),
        (date(2026, 11, 13), "Пт 13.11"),
    ],
)
def test_day_label(day, label):
    assert day_label(day, NOW) == label


def test_describe_settings():
    assert describe_settings(datetime(2026, 12, 31, 15, 0, tzinfo=UTC), 3) == (
        "Ближайшая дата смены: 31.12.2026 18:00 (МСК).\nПромежуток между сменами: 3д."
    )

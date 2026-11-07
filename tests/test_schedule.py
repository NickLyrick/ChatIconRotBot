"""Tests for :mod:`src.utility.schedule`: dates in the chat's time zone."""

from datetime import date, datetime, timedelta, timezone

import pytest

from src.scheduler.runner import next_rotation_date
from src.utility.schedule import (
    DEFAULT_TIMEZONE,
    MAX_DELTA_DAYS,
    TIMEZONE_CHOICES,
    available_hours,
    chat_today,
    day_label,
    describe_settings,
    describe_zone,
    example_rotation_date,
    format_chat_date,
    get_zone,
    localize,
    parse_delta,
    parse_rotation_date,
    parse_timezone,
    rotation_at,
    upcoming_days,
    with_hour,
    zone_offset,
)

UTC = timezone.utc
MSK = "Europe/Moscow"
VLAD = "Asia/Vladivostok"
BERLIN = "Europe/Berlin"

# 15:30 in Moscow on Saturday, 7 November 2026.
NOW = datetime(2026, 11, 7, 12, 30, tzinfo=UTC)


# --- zones --------------------------------------------------------------------


def test_every_menu_zone_is_known():
    for zone in TIMEZONE_CHOICES:
        assert get_zone(zone).zone == zone


@pytest.mark.parametrize("name", [None, "", "Mars/Olympus"])
def test_missing_or_unknown_zone_falls_back_to_moscow(name):
    assert get_zone(name).zone == DEFAULT_TIMEZONE


@pytest.mark.parametrize(
    "text, zone",
    [
        ("Europe/Berlin", BERLIN),
        (" europe/berlin ", BERLIN),
        ("Владивосток", VLAD),
        ("екатеринбург", "Asia/Yekaterinburg"),
        ("UTC", "UTC"),
    ],
)
def test_parse_timezone(text, zone):
    assert parse_timezone(text) == zone


@pytest.mark.parametrize("text", [None, "", "Мордор", "UTC+3", "Europe"])
def test_parse_unknown_timezone(text):
    assert parse_timezone(text) is None


@pytest.mark.parametrize(
    "zone, at, offset",
    [
        (MSK, NOW, "UTC+3"),
        (VLAD, NOW, "UTC+10"),
        ("UTC", NOW, "UTC"),
        ("Asia/Kolkata", NOW, "UTC+5:30"),
        ("America/New_York", NOW, "UTC-5"),
        (BERLIN, datetime(2026, 7, 1, tzinfo=UTC), "UTC+2"),  # summer time
        (BERLIN, NOW, "UTC+1"),
    ],
)
def test_zone_offset(zone, at, offset):
    assert zone_offset(zone, at) == offset


def test_describe_zone():
    assert describe_zone(MSK, NOW) == "Москва (UTC+3)"
    assert describe_zone("UTC", NOW) == "UTC"
    assert describe_zone("America/New_York", NOW) == "America/New_York (UTC-5)"


# --- parse_rotation_date ------------------------------------------------------


def test_date_is_read_in_the_chat_zone_and_stored_in_utc():
    parsed = parse_rotation_date("31/12/2026 18:00", MSK)

    assert parsed == datetime(2026, 12, 31, 15, 0, tzinfo=UTC)
    assert parsed.utcoffset() == timedelta(0)
    assert parse_rotation_date("31/12/2026 18:00", VLAD) == datetime(
        2026, 12, 31, 8, 0, tzinfo=UTC
    )


def test_surrounding_spaces_are_ignored():
    assert parse_rotation_date("  01/02/2027 00:30 ", MSK) == datetime(
        2027, 1, 31, 21, 30, tzinfo=UTC
    )


@pytest.mark.parametrize(
    "text",
    ["", "31.12.2026 18:00", "31/12/2026", "2026/12/31 18:00", "32/12/2026 18:00", "31/12/2026 25:00"],
)
def test_malformed_date_is_rejected(text):
    with pytest.raises(ValueError):
        parse_rotation_date(text, MSK)


def test_time_skipped_by_dst_moves_forward():
    """02:30 does not exist in Berlin on 29 March 2026; it becomes 03:30."""

    moved = localize(datetime(2026, 3, 29, 2, 30), BERLIN)

    assert format_chat_date(moved, BERLIN) == "29.03.2026 03:30 (Берлин)"


# --- format_chat_date / example_rotation_date ---------------------------------


def test_stored_date_is_shown_in_the_chat_zone():
    stored = datetime(2026, 12, 31, 15, 0, tzinfo=UTC)

    assert format_chat_date(stored, MSK) == "31.12.2026 18:00 (Москва)"
    assert format_chat_date(stored, VLAD) == "01.01.2027 01:00 (Владивосток)"
    assert format_chat_date(stored, "America/New_York") == "31.12.2026 10:00 (America/New_York)"


def test_parse_and_format_round_trip():
    for zone in (MSK, VLAD, BERLIN):
        parsed = parse_rotation_date("05/03/2027 09:15", zone)
        assert format_chat_date(parsed, zone).startswith("05.03.2027 09:15")


def test_example_date_is_valid_and_in_the_future():
    now = datetime(2026, 12, 31, 22, 0, tzinfo=UTC)  # already 1 January in Moscow

    example = example_rotation_date(now, MSK)

    assert example == "02/01/2027 18:00"
    assert parse_rotation_date(example, MSK) > now


def test_example_date_follows_the_chat_zone():
    now = datetime(2026, 12, 31, 12, 0, tzinfo=UTC)  # 31.12 in Moscow, 31.12 22:00 in Vladivostok

    assert example_rotation_date(now, MSK) == "01/01/2027 18:00"
    assert example_rotation_date(now, "Pacific/Kiritimati") == "02/01/2027 18:00"  # UTC+14


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


def test_today_follows_the_chat_zone_not_utc():
    late_utc = datetime(2026, 11, 7, 21, 30, tzinfo=UTC)

    assert chat_today(late_utc, MSK) == date(2026, 11, 8)
    assert chat_today(late_utc, "UTC") == date(2026, 11, 7)


def test_rotation_at_is_the_chat_hour_in_utc():
    assert rotation_at(date(2026, 11, 7), 18, MSK) == datetime(2026, 11, 7, 15, 0, tzinfo=UTC)
    assert rotation_at(date(2026, 11, 7), 18, VLAD) == datetime(2026, 11, 7, 8, 0, tzinfo=UTC)


def test_only_future_hours_are_available_today():
    assert available_hours(date(2026, 11, 7), NOW, MSK) == list(range(16, 24))
    assert available_hours(date(2026, 11, 8), NOW, MSK) == list(range(24))
    assert available_hours(date(2026, 11, 6), NOW, MSK) == []
    # 22:30 in Vladivostok.
    assert available_hours(date(2026, 11, 7), NOW, VLAD) == [23]


def test_upcoming_days_start_today():
    days = upcoming_days(NOW, MSK)

    assert days == [date(2026, 11, 7) + timedelta(days=i) for i in range(7)]


def test_upcoming_days_skip_today_after_the_last_hour():
    late = datetime(2026, 11, 7, 20, 30, tzinfo=UTC)  # 23:30 in Moscow

    days = upcoming_days(late, MSK)

    assert days[0] == date(2026, 11, 8)
    assert len(days) == 7


def test_with_hour_keeps_the_day_of_a_future_rotation():
    current = datetime(2026, 11, 10, 15, 0, tzinfo=UTC)  # 10.11 18:00 MSK

    assert format_chat_date(with_hour(current, 9, NOW, MSK), MSK) == "10.11.2026 09:00 (Москва)"


def test_with_hour_uses_the_day_in_the_chat_zone():
    current = datetime(2026, 11, 10, 15, 0, tzinfo=UTC)  # 11.11 01:00 in Vladivostok

    moved = with_hour(current, 9, NOW, VLAD)

    assert format_chat_date(moved, VLAD) == "11.11.2026 09:00 (Владивосток)"


def test_with_hour_moves_to_tomorrow_when_the_hour_has_passed_today():
    current = datetime(2026, 11, 7, 17, 0, tzinfo=UTC)  # today 20:00 MSK

    assert format_chat_date(with_hour(current, 10, NOW, MSK), MSK) == "08.11.2026 10:00 (Москва)"


def test_with_hour_moves_an_overdue_rotation_to_today():
    overdue = datetime(2026, 11, 1, 15, 0, tzinfo=UTC)

    assert format_chat_date(with_hour(overdue, 20, NOW, MSK), MSK) == "07.11.2026 20:00 (Москва)"


def test_with_hour_result_is_always_in_the_future():
    current = datetime(2026, 11, 7, 15, 0, tzinfo=UTC)

    for zone in (MSK, VLAD, "America/New_York"):
        for hour in range(24):
            assert with_hour(current, hour, NOW, zone) > NOW


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
    assert day_label(day, NOW, MSK) == label


def test_day_label_follows_the_chat_zone():
    late = datetime(2026, 11, 7, 20, 0, tzinfo=UTC)  # already 8 November in Vladivostok

    assert day_label(date(2026, 11, 8), late, VLAD) == "Сегодня"
    assert day_label(date(2026, 11, 8), late, MSK) == "Завтра"


def test_describe_settings():
    assert describe_settings(datetime(2026, 12, 31, 15, 0, tzinfo=UTC), 3, MSK) == (
        "Ближайшая дата смены: 31.12.2026 18:00 (Москва).\n"
        "Промежуток между сменами: 3д.\n"
        "Часовой пояс: Москва (UTC+3)."
    )
